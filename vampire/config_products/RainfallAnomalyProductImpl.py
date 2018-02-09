import BaseDataset
import RasterProductImpl
import os
import logging
logger = logging.getLogger(__name__)

class RainfallAnomalyProductImpl(RasterProductImpl.RasterProductImpl):
    """ Initialise RainfallAnomalyProductImpl.

    Implementation class for RainfallAnomalyProduct.
    Initialise object parameters.

    Parameters
    ----------
    country : string
        Region of dataset - country name or 'global'.
    product_date : datetime
        Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
        the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
        the product_date refers to the start of the season (3 month period).
    interval : string
        Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
    vampire_defaults : object
        VAMPIREDefaults object containing VAMPIRE system default values.

    """
    def __init__(self, country, product_date, interval, vampire_defaults):
        super(RainfallAnomalyProductImpl, self).__init__()
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        if self.interval is None:
            self.interval = self.vp.get('CHIRPS_Rainfall_Anomaly', 'default_interval')

        self.chirps_dataset = BaseDataset.BaseDataset.create(dataset_type='CHIRPS', interval=self.interval,
                                                             product_date=self.product_date,
                                                             vampire_defaults=self.vp, region=self.country)
        self.valid_from_date = self.chirps_dataset.start_date()
        self.valid_to_date = self.chirps_dataset.end_date()
        return

    """ Generate VAMPIRE config file header for CHIRPS datasets.

    Parameters
    ----------
    None

    Returns
    -------
    string
        Returns config file header section.

    """
    def generate_header(self):
        config = self.chirps_dataset.generate_header()
        return config


    """ Generate a config file process for the rainfall anomaly product.

    Generate VAMPIRE config file processes for the product including download and crop if specified.

    Parameters
    ----------
    output_dir : string
        Path for product output. If the output_dir is None, the VAMPIRE default rainfall anomaly product directory
        will be used.
    cur_file : string
        Path for current precipitation file. Default is None. If None, cur_dir and cur_pattern will be used to find
        the file.
    cur_dir : string
        Directory path for current precipitation file. Default is None. If cur_file is set, cur_dir is not used.
    cur_pattern : string
        Regular expression pattern for finding current precipitation file. Default is None. If cur_file is set,
        cur_pattern is not used.
    lta_file : string
        Path for long-term average precipitation file. Default is None. If None, lta_dir and lta_pattern will be
        used to find the file.
    lta_dir : string
        Directory path for long-term average precipitation file. Default is None. If lta_file is set, lta_dir is not
        used.
    lta_pattern : string
        Regular expression pattern for finding long-term average precipitation file. Default is None. If lta_file is
        set, lta_pattern is not used.
    output_file : string
        Directory path for output rainfall anomaly file. Default is None. If output_file is set, output_dir is not used.
    output_pattern : string
        Pattern for specifying output filename. Used in conjuction with cur_pattern. Default is None. If output_file is
        set, output_pattern is not used.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_config(self, output_dir=None, cur_file=None, cur_dir=None, cur_pattern=None,
                        lta_file=None, lta_dir=None, lta_pattern=None, output_file=None,
                        output_pattern=None):
        config = """
    ## Processing chain begin - Compute Rainfall Anomaly\n"""
        _c_str, _data_dir = self.chirps_dataset.generate_config(data_dir=None, download=True)
        config += _c_str
		
        if output_file is not None:
            _output_file = output_file
        else:
            _output_file = None

        if output_dir is not None:
            _out_dir = output_dir
        else:
            _out_dir = self.vp.get('CHIRPS_Rainfall_Anomaly', 'output_dir')

        # if cur_file is specified, cur_dir is not used.
        if cur_file is not None:
            _cur_file = cur_file
        else:
            _cur_file = None

        # if cur_dir is specified, it is used with the default pattern to find the current rainfall file
        # if not specified, cur_dir is determined from the default values.
        if cur_dir is not None:
            _cur_dir = cur_dir
        else:
            if self.country.lower() == 'global':
                _cur_dir = os.path.join(self.vp.get('CHIRPS', 'data_dir'), self.interval.capitalize())
            else:
                _cur_dir = os.path.join(self.vp.get('CHIRPS', 'data_dir'), '{interval}\\{ccode}'.format(
                    interval=self.interval, ccode=self.vp.get_country_code(self.country).upper()
                ))

        if self.country.lower() == 'global':
            _output_file_pattern = self.vp.get('CHIRPS_Rainfall_Anomaly',
                                                    'ra_global_output_{0}_pattern'.format(self.interval))
            _cur_file_pattern = self.vp.get('CHIRPS', 'global_{0}_pattern'.format(self.interval))
            _lta_file_pattern = self.vp.get('CHIRPS_Longterm_Average',
                                                 'global_lta_{0}_pattern'.format(self.interval))
        else:
            _output_file_pattern = self.vp.get('CHIRPS_Rainfall_Anomaly',
                                                    'ra_regional_output_{0}_pattern'.format(self.interval))
            _cur_file_pattern = self.vp.get('CHIRPS', 'regional_{0}_pattern'.format(self.interval))
            _lta_file_pattern = self.vp.get('CHIRPS_Longterm_Average',
                                                 'regional_lta_{0}_pattern'.format(self.interval))
        if output_pattern is not None:
            _output_file_pattern = output_pattern
        if cur_pattern is not None:
            _cur_file_pattern = cur_pattern
        if lta_pattern is not None:
            _lta_file_pattern = lta_pattern

        _interval_name = None
        if self.interval.lower() == 'dekad':
            interval_name = 'dekad'
            if int(self.product_date.day) <=10:
                _dekad = 1
            elif int(self.product_date.day) <=20:
                _dekad = 2
            else:
                _dekad = 3
            _cur_file_pattern = _cur_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(_dekad))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{02})',
                                                          '(?P<month>{0})'.format(self.product_date.month))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(_dekad))
        elif self.interval.lower() == 'monthly':
            _interval_name = 'month'
            # replace generic month in pattern with the specific one needed so the correct file is found.
            _cur_file_pattern = _cur_file_pattern.replace('(?P<month>\d{2})',
                                                          '(?P<month>{0})'.format(self.product_date.month))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{2})',
                                                          '(?P<month>{0})'.format(self.product_date.month))
        elif self.interval.lower() == 'seasonal':
            _interval_name = 'season'
            # replace generic season in pattern with the specific one needed so the correct file is found.
            #TODO need to get the season somehow - is product date the first month of the season? last month?
            _season = '010203'
            _lta_file_pattern = _lta_file_pattern.replace('(?P<season>\d{6})', '(?P<season>{0})'.format(_season))
            _cur_file_pattern = _cur_file_pattern.replace('(?P<season>\d{6})', '(?P<season>{0})'.format(_season))
        else:
            logger.error('Unrecognised interval {0}. Unable to generate rainfall anomaly config.'.format(
                self.interval))
            raise ValueError, 'Unrecognised interval {0}. Unable to generate rainfall anomaly config.'.format(
                self.interval)

        # replace generic year in pattern with the specific one needed so the correct file is found.
        _cur_file_pattern = _cur_file_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))

        # if lta_file is specified, lta_dir is not used.
        if lta_file is not None:
            _lta_file = lta_file
        else:
            _lta_file = None

        # if lta_dir is specified, it is used with the default pattern to find the long-term average rainfall file
        # if not specified, lta_dir is determined from the default values.
        if lta_dir is not None:
            _lta_dir = lta_dir
        else:
            if self.country.lower() == 'global':
                _lta_dir = os.path.join(self.vp.get('CHIRPS', 'global_product_dir'),
                                        '{interval}\\Statistics_By{interval_name}'.format(
                                        interval=self.interval.capitalize(), interval_name=_interval_name.capitalize()))
            elif self.country == self.vp.get_home_country():
                _lta_dir = os.path.join(self.vp.get('CHIRPS', 'home_country_product_dir'),
                                        '{interval}\\Statistics_By{interval_name}'.format(
                                        interval=self.interval.capitalize(), interval_name=_interval_name.capitalize()))
            else:
                _lta_dir = os.path.join(self.vp.get('CHIRPS', 'regional_product_dir_prefix'),
                                        '{suffix}\\{interval}\\Statistics_By{interval_name}'.format(
                                        suffix=self.vp.get('CHIRPS', 'regional_product_dir_suffix'),
                                        interval=self.interval.capitalize(),
                                        interval_name=_interval_name.capitalize()))


        config += self._generate_rainfall_anomaly_section(cur_file=_cur_file, cur_dir=_cur_dir,
                                                         cur_pattern=_cur_file_pattern, lta_file=_lta_file,
                                                         lta_dir=_lta_dir, lta_pattern=_lta_file_pattern,
                                                         output_file=_output_file, output_dir=_out_dir,
                                                         output_pattern=_output_file_pattern)
        config += """
    ## Processing chain end - Compute Rainfall Anomaly"""

        self.product_file = None
        self.product_dir = _out_dir
        self.product_pattern = self.vp.get('Days_Since_Last_Rain', 'regional_dslr_pattern')
        self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
        return config


    """ Generate a config file process for the rainfall anomaly product.

    Internal method to actually generate rainfall anomaly VAMPIRE config file process.

    Parameters
    ----------
    cur_file : string
        Path for current precipitation file.
    cur_dir : string
        Directory path for current precipitation file.
    cur_pattern : string
        Regular expression pattern for finding current precipitation file.
    lta_file : string
        Path for long-term average precipitation file.
    lta_dir : string
        Directory path for long-term average precipitation file.
    lta_pattern : string
        Regular expression pattern for finding long-term average precipitation file.
    output_file : string
        Directory path for output rainfall anomaly file.
    output_dir : string
        Path for product output.
    output_pattern : string
        Pattern for specifying output filename.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def _generate_rainfall_anomaly_section(self, cur_file, cur_dir, cur_pattern, lta_file, lta_dir, lta_pattern,
                                          output_file, output_dir, output_pattern):
        config = """
    # compute rainfall anomaly
    - process: Analysis
      type: rainfall_anomaly"""
        if cur_file is not None:
            config += """
      current_file: {cur_file}""".format(cur_file=cur_file)
        else:
            config += """
      current_dir: {cur_dir}
      current_file_pattern: '{cur_pattern}'""".format(cur_dir=cur_dir, cur_pattern=cur_pattern)

        if lta_file is not None:
            config += """
      longterm_avg_file: {lta_file}""".format(lta_file=lta_file)
        else:
            config += """
      longterm_avg_dir: {lta_dir}
      longterm_avg_file_pattern: '{lta_pattern}'""".format(lta_dir=lta_dir, lta_pattern=lta_pattern)

        if output_file is not None:
            config += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            config += """
      output_dir: {out_dir}
      output_file_pattern: '{out_pattern}'""".format(out_dir=output_dir, out_pattern=output_pattern)

        return config


    #     year = start_date.strftime("%Y")
    #     month = start_date.strftime("%m")
    #     day = start_date.strftime("%d")
    #     if country == 'Global':
    #         crop = False
    #
    #     # if output_file is specified, it will override the location of the output file.
    #     # if output_dir is specified, the rainfall anomaly result will be stored here.
    #     # the filename will be generated from the default pattern.
    #     if output_dir is not None:
    #         _out_dir = output_dir
    #     else:
    #         _out_dir = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'output_dir')
    #
    #     # if cur_file is specified, cur_dir is not used.
    #     # if cur_dir is specified, it is used with the default pattern to find the current rainfall file
    #     # if not specified, cur_dir is determined from the default values.
    #     if cur_dir is not None:
    #         _cur_dir = cur_dir
    #     else:
    #         if country == 'Global':
    #             _cur_dir = os.path.join(self.vampire.get('CHIRPS', 'data_dir'), interval.capitalize())
    #         else:
    #             _cur_dir = os.path.join(self.vampire.get('CHIRPS', 'data_dir'), '{interval}\\{ccode}'.format(
    #                 interval=interval, ccode=self.vampire.get_country_code(country).upper()
    #             ))
    #     if interval == 'monthly':
    #         _interval_name = 'month'
    #         _file_pattern = self.vampire.get('CHIRPS', 'global_monthly_pattern')
    #         if country == 'Global':
    #             _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_global_output_monthly_pattern')
    #             _crop_output_pattern = ''
    #             _cur_file_pattern = self.vampire.get('CHIRPS', 'global_monthly_pattern')
    #             _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_monthly_pattern')
    #         else:
    #             _crop_output_pattern = '{0}{1}'.format(
    #                 self.vampire.get_country_code(country).lower(),
    #                 self.vampire.get('CHIRPS', 'crop_regional_output_monthly_pattern'))
    #             _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_output_monthly_pattern')
    #             _cur_file_pattern = self.vampire.get('CHIRPS', 'regional_monthly_pattern')
    #             _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'regional_lta_monthly_pattern')
    #         # replace generic month in pattern with the specific one needed so the correct file is found.
    #         _cur_file_pattern = _cur_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(month))
    #         _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(month))
    #     elif interval == 'seasonal':
    #         _interval_name = "season"
    #         _file_pattern = self.vampire.get('CHIRPS', 'global_seasonal_pattern')
    #         if country == 'Global':
    #             _crop_output_pattern = ''
    #             _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_global_output_seasonal_pattern')
    #             _cur_file_pattern = self.vampire.get('CHIRPS', 'global_seasonal_pattern')
    #             _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_seasonal_pattern')
    #         else:
    #             _crop_output_pattern = '{0}{1}'.format(
    #                 self.vampire.get_country_code(country).lower(),
    #                 self.vampire.get('CHIRPS', 'crop_regional_output_seasonal_pattern'))
    #             _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_output_seasonal_pattern')
    #             _cur_file_pattern = self.vampire.get('CHIRPS', 'regional_seasonal_pattern')
    #             _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'regional_lta_seasonal_pattern')
    #         # replace generic season in pattern with the specific one needed so the correct file is found.
    #         _lta_file_pattern = _lta_file_pattern.replace('(?P<season>\d{6})', '(?P<season>{0})'.format(season))
    #         _cur_file_pattern = _cur_file_pattern.replace('(?P<season>\d{6})', '(?P<season>{0})'.format(season))
    #
    #     elif interval == 'dekad':
    #         _file_pattern = self.vampire.get('CHIRPS', 'global_dekad_pattern')
    #         _interval_name = interval
    #         if country == 'Global':
    #             _crop_output_pattern = ''
    #             _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_global_output_dekad_pattern')
    #             _cur_file_pattern = self.vampire.get('CHIRPS', 'global_dekad_pattern')
    #             _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_dekad_pattern')
    #         else:
    #             _crop_output_pattern = '{0}{1}'.format(
    #                 self.vampire.get_country_code(country).lower(),
    #                 self.vampire.get('CHIRPS', 'crop_regional_output_dekad_pattern'))
    #             _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_output_dekad_pattern')
    #             _cur_file_pattern = self.vampire.get('CHIRPS', 'regional_dekad_pattern')
    #             _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'regional_lta_dekad_pattern')
    #         # replace generic month and dekad in pattern with the specific one needed so the correct file is found.
    #         _cur_file_pattern = _cur_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(month))
    #         if int(day) <=10:
    #             _dekad = 1
    #         elif int(day) <=20:
    #             _dekad = 2
    #         else:
    #             _dekad = 3
    #         _cur_file_pattern = _cur_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(_dekad))
    #         _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{02})', '(?P<month>{0})'.format(month))
    #         _lta_file_pattern = _lta_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(_dekad))
    #     else:
    #         raise ValueError, 'Unrecognised interval {0}. Unable to generate rainfall anomaly config.'.format(
    #             interval)
    #         # _interval_name = interval
    #         # _crop_output_pattern = "'{0}".format(country.lower()) + "_cli_{product}.{year}.{month}{extension}'"
    #         # _file_pattern = ''
    #         # _cur_file_pattern = ''
    #
    #     # replace generic year in pattern with the specific one needed so the correct file is found.
    #     _cur_file_pattern = _cur_file_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(year))
    #
    #     # directory for downloaded CHIRPS files
    #     _dl_output = "{0}\\{1}".format(self.vampire.get('CHIRPS','data_dir'),
    #                                    interval.capitalize())
    #
    #     _num_yrs = int(self.vampire.get('CHIRPS_Longterm_Average', 'lta_date_range').split('-')[1]) - int(
    #         self.vampire.get('CHIRPS_Longterm_Average', 'lta_date_range').split('-')[0]
    #     )
    #     _boundary_file = None
    #     _country_code = self.vampire.get_country_code(country)
    #     if country != 'Global':
    #         _boundary_file = os.path.join(os.path.join(self.vampire.get('CHIRPS', 'regional_boundary_prefix'),
    #                                                    self.vampire.get('CHIRPS', 'regional_boundary_suffix')),
    #                                       '{0}{1}'.format(_country_code.lower(),
    #                                                       self.vampire.get('CHIRPS', 'regional_boundary_file')))
    #         #self.vampire.get_country(country)['chirps_boundary_file']
    #
    #     # if lta_file is specified, lta_dir is not used.
    #     # if lta_dir is specified, it is used with the default pattern to find the long-term average rainfall file
    #     # if not specified, lta_dir is determined from the default values.
    #     if lta_dir is not None:
    #         _lta_dir = lta_dir
    #     else:
    #         if country == 'Global':
    #             _lta_dir = os.path.join(self.vampire.get('CHIRPS', 'global_product_dir'),
    #                                     '{interval}\\Statistics_By{interval_name}'.format(
    #                 interval=interval.capitalize(), interval_name=_interval_name.capitalize()))
    #         elif country == self.vampire.get_home_country():
    #             _lta_dir = os.path.join(self.vampire.get('CHIRPS', 'home_country_product_dir'),
    #                                     '{interval}\\Statistics_By{interval_name}'.format(
    #                                         interval=interval.capitalize(), interval_name=_interval_name.capitalize()))
    #         else:
    #             _lta_dir = os.path.join(self.vampire.get('CHIRPS', 'regional_product_dir_prefix'),
    #                                     '{suffix}\\{interval}\\Statistics_By{interval_name}'.format(
    #                                         suffix=self.vampire.get('CHIRPS', 'regional_product_dir_suffix'),
    #                                         interval=interval.capitalize(),
    #                                         interval_name=_interval_name.capitalize()))
    #
    #     config = """
    # ## Processing chain begin - Compute Rainfall Anomaly\n"""
    #     if download:
    #         # add commands to download data
    #         config += self.generate_download_section(interval=interval, data_dir=_dl_output,
    #                                                       start_date=start_date, end_date=start_date)
    #     if crop:
    #         # add commands to crop global data to region
    #         config += self.generate_crop_section(country=country, input_dir=_dl_output,
    #                                                   output_dir=os.path.join(_dl_output, _country_code.upper()),
    #                                                   file_pattern=_file_pattern, output_pattern=_crop_output_pattern,
    #                                                   boundary_file=_boundary_file, no_data=True
    #                                                  )
    #
    #     config += """
    # # compute rainfall anomaly
    # - process: Analysis
    #   type: rainfall_anomaly"""
    #     if cur_file is not None:
    #         file_string += """
    #   current_file: {cur_file}""".format(cur_file=cur_file)
    #     else:
    #         config += """
    #   current_dir: {cur_dir}
    #   current_file_pattern: '{cur_pattern}'""".format(cur_dir=_cur_dir, cur_pattern=_cur_file_pattern)
    #
    #     if lta_file is not None:
    #         file_string += """
    #   longterm_avg_file: {lta_file}""".format(lta_file=lta_file)
    #     else:
    #         config += """
    #   longterm_avg_dir: {lta_dir}
    #   longterm_avg_file_pattern: '{lta_pattern}'""".format(lta_dir=_lta_dir, lta_pattern=_lta_file_pattern)
    #
    #     if output_file is not None:
    #         config += """
    #   output_file: {output_file}""".format(output_file=output_file)
    #     else:
    #         config += """
    #   output_dir: {out_dir}
    #   output_file_pattern: '{out_pattern}'""".format(out_dir=_out_dir, out_pattern=_output_file_pattern)
    #
    #     config += """
    # ## Processing chain end - Compute Rainfall Anomaly
    #     """
    #
    #    return config
