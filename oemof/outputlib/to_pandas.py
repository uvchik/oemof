#!/usr/bin/python
# -*- coding: utf-8

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# TODO:
# - Add storages to column "other"
# - Create some "standard-slices" for plots e.g. all inputs of a specific bus
# - Make dataframe creation and plotting configurable via params_dc{}

class EnergySystemDataFrame:
    """Creates a multi-indexed pandas dataframe from a solph result object
    and holds methods to plot subsets of the data

    Note
    ----
    This is so far only a rough sketch and serves as a base for discussion.

    Parameters
    ----------
    result_object : dictionary
        solph result objects
    idx_start_date : string
        Start date of the dataframe date index e.g. "2016-01-01 00:00:00"
    ixd_date_freq : string
        Frequency for the dataframe date index e.g. "H" for hours

    Attributes
    ----------
    result_object : dictionary
        solph result objects
    idx_start_date : string
        Start date of the dataframe date index e.g. "2016-01-01 00:00:00"
    ixd_date_freq : string
        Frequency for the dataframe date index e.g. "H" for hours
    data_frame : pandas dataframe 
        Multi-indexed pandas dataframe holding the data from the result object
    """
    def __init__(self, **kwargs):
        # default values if not arguments are passed
        kwargs.setdefault('ixd_date_freq', 'H') 

        self.result_object = kwargs.get('result_object')
        self.idx_start_date = kwargs.get('idx_start_date')
        self.ixd_date_freq = kwargs.get('ixd_date_freq')
        self.data_frame = None
        if not (self.data_frame): self.data_frame = self.create()

    def create(self): 
        """ Method for creating a multi-index pandas dataframe of
        the result object

        Parameters
        ----------
        self : EnergySystemDataFrame() instance
        """
        df = pd.DataFrame(columns=['bus_uid', 'bus_type', 'type',
                                   'obj_uid', 'datetime', 'val'])
        for e, o in self.result_object.items():
            if 'Bus' in str(e.__class__):
                row = pd.DataFrame()
                # inputs
                for i in e.inputs:
                    if i in self.result_object:
                        row['bus_uid'] = [e.uid]
                        row['bus_type'] = [e.type]
                        row['type'] = ['input']
                        row['obj_uid'] = [i.uid]
                        row['datetime'] = \
                            [pd.date_range(self.idx_start_date,
                             periods=len(self.result_object[i].get(e)),
                             freq=self.ixd_date_freq)]
                        row['val'] = [self.result_object[i].get(e)]
                        df = df.append(row)
                # outputs
                for k, v in o.items():
                    # skip self referenced entries (duals, etc.) and
                    # string keys to put them into "other"
                    if k is not e and not (isinstance(k, str)):
                        row['bus_uid'] = [e.uid]
                        row['bus_type'] = [e.type]
                        row['type'] = ['output']
                        row['obj_uid'] = [k.uid]
                        row['datetime'] = \
                            [pd.date_range(self.idx_start_date,
                             periods=len(v), freq=self.ixd_date_freq)]
                        row['val'] = [v]
                        df = df.append(row)
                # other
                for k, v in o.items():
                    row['bus_uid'] = [e.uid]
                    row['bus_type'] = [e.type]
                    row['type'] = ['other']
                    # self referenced entries (duals, etc.) in else block
                    if k is not e and isinstance(k, str):
                        row['obj_uid'] = [k]
                        row['datetime'] = \
                            [pd.date_range(self.idx_start_date,
                             periods=len(v), freq=self.ixd_date_freq)]
                        row['val'] = [v]
                        df = df.append(row)
                    else:
                        row['obj_uid'] = ['duals']
                        row['datetime'] = \
                            [pd.date_range(self.idx_start_date,
                             periods=len(v), freq=self.ixd_date_freq)]
                        row['val'] = [v]
                        df = df.append(row)
        
        # split date and value lists columns into rows (long format)
        df_long = pd.DataFrame()
        for index, cols in df.iterrows():
            df_extract = pd.DataFrame.from_dict(
                         {'datetime': cols.ix['datetime'],
                         'val': cols.ix['val']})
            df_extract = pd.concat(
                [df_extract, cols.drop(['datetime', 'val']).to_frame().T],
                 axis=1).fillna(method='ffill').fillna(method='bfill')
            df_long = pd.concat([df_long, df_extract], ignore_index=True)
        
        # create multiindexed dataframe
        arrays = [df_long['bus_uid'], df_long['bus_type'], df_long['type'],
                  df_long['obj_uid'], df_long['datetime']]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples,
                                          names=['bus_uid', 'bus_type', 'type',
                                                 'obj_uid', 'datetime'])
        df_multiindex = pd.DataFrame(df_long['val'].values,
                                    columns=['val'], index=index)
        
        # sort MultiIndex to work correctly
        df_multiindex.sort_index(inplace=True)

        return df_multiindex

    def plot_bus(self, **kwargs):
        """ Method for plotting all inputs/outputs of a bus

        Parameters
        ----------
        bus_uid : string
        bus_type : string (e.g. "el" or "gas")
        type : string (input/output/other)
        date_from : string (Start date selection e.g. "2016-01-01 00:00:00")
        date_to : string (End date selection e.g. "2016-03-01 00:00:00")
        """
        kwargs.setdefault('bus_uid', None)
        kwargs.setdefault('bus_type', None)
        kwargs.setdefault('type', None)
        kwargs.setdefault('date_from', None)
        kwargs.setdefault('date_to', None)
        kwargs.setdefault('kind', 'line')        
        kwargs.setdefault('title', 'Connected components')
        kwargs.setdefault('xlabel', 'Date')
        kwargs.setdefault('ylabel', 'Power in MW')
        kwargs.setdefault('date_format', '%d-%m-%Y')
        kwargs.setdefault('tick_distance', 24)
        kwargs.setdefault('subplots', False)
        kwargs.setdefault('colormap', 'Spectral')
        kwargs.setdefault('mpl_style', 'ggplot')
              
        # slicing        
        idx = pd.IndexSlice     
        subset = self.data_frame.loc[idx[[kwargs.get('bus_uid')],
                                         [kwargs.get('bus_type')],
                                         [kwargs.get('type')],
                                          :,
                                          slice(
                                          pd.Timestamp(kwargs.get('date_from')),
                                          pd.Timestamp(kwargs.get('date_to')))]]
        # unstacking object/component level to get columns
        subset = subset.unstack(level='obj_uid')
        
        # plotting: set matplotlib style
        mpl.style.use(kwargs.get('mpl_style'))

        # plotting: basic pandas plot      
        subset.plot(kind=kwargs.get('kind'), colormap=kwargs.get('colormap'),
                    title=kwargs.get('title'), linewidth='2',
                    subplots=kwargs.get('subplots'))
        # plotting: adjustments
        dates = subset.index.get_level_values('datetime').unique()
        [(ax.set_ylabel(kwargs.get('ylabel')),
          ax.set_xlabel(kwargs.get('xlabel')),
          #ax.set_xticks(range(0,len(dates),1), minor=True),
          ax.set_xticks(range(0,len(dates),kwargs.get('tick_distance')),
                        minor=False),
          ax.set_xticklabels(
              [item.strftime('%d-%m-%Y')
               for item in dates.tolist()[0::kwargs.get('tick_distance')]],
              rotation=0,minor=False),
          ax.legend(loc='upper right')
          )
         for ax in plt.gcf().axes]
