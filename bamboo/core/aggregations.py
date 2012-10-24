from pandas import DataFrame, Series


class Aggregation(object):
    """
    Abstract class for all aggregations.
    """

    def __init__(self, name, groups, dframe):
        self.name = name
        self.groups = groups
        self.dframe = dframe

    def _eval(self, columns):
        self.columns = columns
        self.column = columns[0]
        return self.group() if self.groups else self.agg()

    def group(self):
        """
        For when aggregation is called with a group parameter.
        """
        groupby = self.dframe[self.groups].join(
            self.column).groupby(self.groups, as_index=False)
        return groupby.agg(self.formula_name)

    def agg(self):
        """
        For when aggregation is called without a group parameter.
        """
        result = float(self.column.__getattribute__(self.formula_name)())
        return DataFrame({self.name: Series([result])})


class MultiColumnAggregation(Aggregation):
    """
    Interface for aggregations that create multiple columns.
    """
    def _reduce(self, dframe, columns):
        self.columns = columns
        self.column = columns[0]
        new_dframe = self.agg()
        for column in new_dframe.columns:
            dframe[column] += new_dframe[column]
        dframe[self.name] = self._agg_dframe(dframe)
        return dframe

    def _name_for_idx(self, idx):
        return '%s_%s' % (self.name, {
            0: 'numerator',
            1: 'denominator',
        }[idx])

    def _build_dframe(self, dframe, columns):
        for idx, column in enumerate(columns):
            column.name = self._name_for_idx(idx)
            dframe = dframe.join(column)

        return dframe

    def _agg_dframe(self, dframe):
        return dframe[self._name_for_idx(0)].apply(float) /\
            dframe[self._name_for_idx(1)]


class MaxAggregation(Aggregation):
    """
    Calculate the maximum.
    """

    formula_name = 'max'


class MeanAggregation(MultiColumnAggregation):
    """
    Calculate the arithmetic mean.
    """

    formula_name = 'mean'

    def agg(self):
        dframe = DataFrame(index=[0])

        columns = [
            Series([col]) for col in [self.column.sum(), len(self.column)]]
        dframe = self._build_dframe(dframe, columns)

        dframe = DataFrame([dframe.sum().to_dict()])
        column = self._agg_dframe(dframe, self.name)
        column.name = self.name
        return dframe.join(column)

    def group(self):
        dframe = self.dframe[self.groups]

        dframe = self._build_dframe(
            dframe, [self.column, Series([1] * len(self.column))])
        groupby = dframe.groupby(self.groups, as_index=False)
        aggregated_dframe = groupby.sum()

        new_column = self._agg_dframe(aggregated_dframe)
        new_column.name = self.name

        dframe = aggregated_dframe.join(new_column)

        return dframe


class MedianAggregation(Aggregation):
    """
    Calculate the median.
    """

    formula_name = 'median'


class MinAggregation(Aggregation):
    """
    Calculate the minimum.
    """

    formula_name = 'min'


class SumAggregation(Aggregation):
    """
    Calculate the sum.
    """

    formula_name = 'sum'

    def _reduce(self, dframe, columns):
        self.columns = columns
        self.column = columns[0]
        dframe[self.name] += self.agg()[self.name]
        return dframe


class RatioAggregation(MultiColumnAggregation):
    """
    Calculate the ratio. Columns with N/A for either the numerator or
    denominator are ignored.  This will store associated numerator and
    denominator columns.
    """

    formula_name = 'ratio'

    def group(self):
        # name of formula
        dframe = self.dframe[self.groups]

        dframe = self._build_dframe(dframe, self.columns)

        groupby = dframe.groupby(self.groups, as_index=False)
        aggregated_dframe = groupby.sum()

        new_column = self._agg_dframe(aggregated_dframe)

        new_column.name = self.name
        dframe = aggregated_dframe.join(new_column)

        return dframe

    def agg(self):
        dframe = DataFrame(index=self.column.index)

        dframe = self._build_dframe(dframe, self.columns)
        column_names = [self._name_for_idx(i) for i in xrange(0, 2)]
        dframe = dframe.dropna(subset=column_names)

        dframe = DataFrame([dframe.sum().to_dict()])
        column = self._agg_dframe(dframe)
        column.name = self.name
        return dframe.join(column)


AGGREGATIONS = dict([
    (cls.formula_name, cls) for cls in
    Aggregation.__subclasses__() + MultiColumnAggregation.__subclasses__()
    if hasattr(cls, 'formula_name')])
