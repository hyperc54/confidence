# Copyright 2017-2020 Spotify AB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import (Union, Iterable, Tuple, Dict)

from pandas import DataFrame

from .chartify_grapher import ChartifyGrapher
from .statsmodels_computer import ZTestComputer
from ..abstract_base_classes.confidence_abc import ConfidenceABC
from ..abstract_base_classes.confidence_computer_abc import \
    ConfidenceComputerABC
from ..abstract_base_classes.confidence_grapher_abc import ConfidenceGrapherABC
from ..confidence_utils import (validate_categorical_columns, listify,
                                get_all_group_columns, validate_data)
from ..constants import BONFERRONI, NIM_TYPE
from ...chartgrid import ChartGrid
from ..frequentist.sample_ratio_test import sample_ratio_test


class ZTest(ConfidenceABC):

    def __init__(self,
                 data_frame: DataFrame,
                 numerator_column: str,
                 numerator_sum_squares_column: Union[str, None],
                 denominator_column: str,
                 categorical_group_columns: Union[str, Iterable],
                 ordinal_group_column: Union[str, None] = None,
                 interval_size: float = 0.95,
                 correction_method: str = BONFERRONI,
                 confidence_computer: ConfidenceComputerABC = None,
                 confidence_grapher: ConfidenceGrapherABC = None):

        validate_categorical_columns(categorical_group_columns)
        self._df = data_frame
        self._numerator = numerator_column
        self._numerator_sumsq = numerator_sum_squares_column
        self._denominator = denominator_column
        self._categorical_group_columns = listify(categorical_group_columns)
        self._ordinal_group_column = ordinal_group_column

        self._all_group_columns = get_all_group_columns(
            self._categorical_group_columns,
            self._ordinal_group_column)
        validate_data(self._df,
                      self._numerator,
                      self._numerator_sumsq,
                      self._denominator,
                      self._all_group_columns,
                      self._ordinal_group_column)

        self._confidence_computer = confidence_computer \
            if confidence_computer is not None \
            else ZTestComputer(
                data_frame=self._df,
                numerator_column=self._numerator,
                numerator_sum_squares_column=self._numerator_sumsq,
                denominator_column=self._denominator,
                categorical_group_columns=self._categorical_group_columns,
                ordinal_group_column=self._ordinal_group_column,
                interval_size=interval_size,
                correction_method=correction_method.lower())

        self._confidence_grapher = confidence_grapher if confidence_grapher \
            is not None \
            else ChartifyGrapher(
                data_frame=self._df,
                numerator_column=self._numerator,
                denominator_column=self._denominator,
                categorical_group_columns=self._categorical_group_columns,
                ordinal_group_column=self._ordinal_group_column)

    def summary(self) -> DataFrame:
        return self._confidence_computer.compute_summary()

    def difference(self,
                   level_1: Union[str, Tuple],
                   level_2: Union[str, Tuple],
                   absolute: bool = True,
                   groupby: Union[str, Iterable] = None,
                   non_inferiority_margins: NIM_TYPE = None
                   ) -> DataFrame:
        return self._confidence_computer.compute_difference(
            level_1,
            level_2,
            absolute,
            groupby,
            non_inferiority_margins)

    def multiple_difference(self, level: Union[str, Tuple],
                            absolute: bool = True,
                            groupby: Union[str, Iterable] = None,
                            level_as_reference: bool = False,
                            non_inferiority_margins: NIM_TYPE = None
                            ) -> DataFrame:
        return self._confidence_computer.compute_multiple_difference(
            level,
            absolute,
            groupby,
            level_as_reference,
            non_inferiority_margins)

    def summary_plot(self,
                     groupby: Union[str, Iterable] = None) -> ChartGrid:
        summary_df = self.summary()
        graph = self._confidence_grapher.plot_summary(summary_df, groupby)
        return graph

    def difference_plot(self,
                        level_1: Union[str, Tuple],
                        level_2: Union[str, Tuple],
                        absolute: bool = True,
                        groupby: Union[str, Iterable] = None,
                        non_inferiority_margins: NIM_TYPE = None,
                        use_adjusted_intervals: bool = False
                        ) -> ChartGrid:
        difference_df = self.difference(level_1,
                                        level_2,
                                        absolute,
                                        groupby,
                                        non_inferiority_margins)
        chartgrid = self._confidence_grapher.plot_difference(
            difference_df,
            absolute,
            groupby,
            non_inferiority_margins,
            use_adjusted_intervals)
        return chartgrid

    def multiple_difference_plot(self,
                                 level: Union[str, Tuple],
                                 absolute: bool = True,
                                 groupby: Union[str, Iterable] = None,
                                 level_as_reference: bool = False,
                                 non_inferiority_margins: NIM_TYPE = None,
                                 use_adjusted_intervals: bool = False
                                 ) -> ChartGrid:
        difference_df = self.multiple_difference(level,
                                                 absolute,
                                                 groupby,
                                                 level_as_reference,
                                                 non_inferiority_margins)
        chartgrid = self._confidence_grapher.plot_multiple_difference(
            difference_df,
            absolute,
            groupby,
            level_as_reference,
            non_inferiority_margins,
            use_adjusted_intervals)
        return chartgrid

    def sample_ratio_test(self, expected_proportions: Dict
                          ) -> Tuple[float, DataFrame]:
        return sample_ratio_test(self._df,
                                 all_group_columns=self._all_group_columns,
                                 denominator=self._denominator,
                                 expected_proportions=expected_proportions)
