import RasterDatasetImpl
import datetime
import dateutil.rrule
import dateutil.relativedelta
import os
import logging
logger = logging.getLogger(__name__)

class GlobalForecastSystemDatasetImpl(RasterDatasetImpl.RasterDatasetImpl):
    """ Initialise GlobalForecastSystemDatasetImpl object.

    Implementation class for GlobalForecastSystemDataset.
    Initialise object parameters and calculate start and end dates for dataset using product_date and interval.

    Parameters
    ----------
    interval : string
        Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
    product_date : datetime
        Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
        the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
        the product_date refers to the start of the season (3 month period).
    """
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        logger.debug('Initialising GFS dataset')
        super(GlobalForecastSystemDatasetImpl, self).__init__()
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        self.region = region

        if self.interval.lower() == 'daily':
            self.start_date = product_date
            self.end_date = product_date
        elif self.interval.lower() == 'dekad':
            self.start_date = datetime.timedelta(days=-10)
            self.end_date = product_date
        elif self.interval.lower() == 'monthly':
            self.start_date = datetime.datetime(product_date.year, product_date.month, 1) # ensure start date is first day of month
            self.end_date = self.start_date + dateutil.relativedelta.relativedelta(months=1,days=-1) # ensure end_date is last day of month
        elif self.interval.lower() == 'seasonal':
            self.start_date = product_date
            self.end_date = self.start_date + dateutil.relativedelta.relativedelta(months=3, days=-1) # set end_date as last day of third month
        else:
            logger.error("Interval '{0}' is not a valid GFS dataset interval".format(self.interval))
            raise ValueError
#        self.start_date = params['start_date']
#        self.country = params['country']
        return

    """ Generate a config file process for the dataset.

    Generate VAMPIRE config file process(es) for the dataset including download and crop if specified.

    Parameters
    ----------
    data_dir : string
        Path for downloaded data. The data will be stored in this path under a directory with the interval name. If the
        data_dir is None, the VAMPIRE default download directory will be used.
    download : boolean
        Flag indicating whether data should be downloaded. Default is True.
    crop : boolean
        Flag indicating whether data should be cropped to region. Default is True.
    crop_dir : string
        Path where cropped data will be stored. If None, the region code will be appended to the download data path.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_config(self, data_dir=None, variable=None, level=None, forecast_hr=None, download=True, crop=True,
                        crop_dir=None, accumulate_days=None):
        logger.debug('GlobalForecastSystemDataset generate_config')
        config = ''
        if data_dir is None:
            _data_dir = self.vp.get('GFS', 'data_dir')
        else:
            _data_dir = data_dir
        _download_dir = os.path.join(_data_dir, self.interval.capitalize()) #"{0}\\{1}".format(_data_dir, self.interval.capitalize())

        if download:
            config += self._generate_download_section(data_dir=_download_dir)
            _data_dir = _download_dir

        if accumulate_days is not None:
            if forecast_hr is None:
                _fc_hr = self.vp.get('GFS', 'model_cycle_runtime')
            else:
                _fc_hr = forecast_hr
            _raw_dir = os.path.join(_download_dir, '{0:0>4}{1:0>2}{2:0>2}{3:0>2}'.format(self.product_date.year,
                                                                                         self.product_date.month,
                                                                                         self.product_date.day,
                                                                                         _fc_hr))
            _data_pattern = self.vp.get('GFS', 'global_raw_pattern')
            _accum_pattern = self.vp.get('GFS', 'global_output_accum_pattern')
            config += self._generate_accumulate_section(data_dir=_raw_dir, data_pattern=_data_pattern,
                                                        output_dir=_download_dir, output_pattern=_accum_pattern,
                                                        accumulate_days=accumulate_days)
            _data_dir = _download_dir

        if crop:
            _country_code = self.vp.get_country_code(self.region)
            if crop_dir is None:
                _crop_dir = os.path.join(_data_dir, _country_code.upper())
            else:
                _crop_dir = crop_dir
            _data_dir = _crop_dir

            if self.region is not None and self.region.lower() is not 'global':
                # self.region should contain country name
                config += """
    # Crop data to {country}""".format(country=self.region)
                _input_pattern = self.vp.get('GFS', 'global_accum_pattern')
                _output_pattern = '{0}{1}'.format(self.vp.get_country_code(self.region).lower(),
                                                  self.vp.get('GFS',
                                                              'regional_output_accum_pattern'))
                _boundary_file = self.vp.get_country('{0}'.format(self.region))['chirps_boundary_file']
                config += self.generate_crop_section(_download_dir, _crop_dir, _input_pattern, _output_pattern, _boundary_file)

        return config, _data_dir


    """ Generate VAMPIRE config file header for GFS datasets.

    Parameters
    ----------
    None

    Returns
    -------
    string
        Returns config file header section.

    """
    def generate_header(self):
        config = """"""
        return config

    """ Generate download process section for GFS dataset.

    Generate VAMPIRE config file process for GFS dataset download.

    Parameters
    ----------
    data_dir : string
        Path for downloaded data. The data will be stored in this path under a directory with the interval name. If the
        data_dir is None, the VAMPIRE default download directory will be used.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def _generate_download_section(self, data_dir):
        config = """
    # download GFS forecast data
    - process: GFS
      type: download
      output_dir: {output_dir}""".format(output_dir=data_dir)
        # if start and end dates are specified, only download between these dates
        if self.product_date is not None:
            year = self.start_date.strftime("%Y")
            month = self.start_date.strftime("%m")
            day = self.start_date.strftime("%d")
            # use 1st of start_date month to make sure end month is also included
            _first_date = self.start_date.replace(self.start_date.year, self.start_date.month, self.product_date.day)
            dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=_first_date).between(_first_date,
                                                                                              self.end_date, inc=True)
            config += """
      dates: ["""
            for d in dates:
                config += '{year}-{month}-{day},'.format(year=d.strftime("%Y"), month=d.strftime("%m"),
                                                         day=d.strftime("%d"))
            config = config[:-1]
            config += """]
            """
        return config

    def _generate_accumulate_section(self, data_dir, data_pattern, output_dir, output_pattern, accumulate_days):
        config = """
    # accumulate GFS forecast data to {accumulate_days} days
    - process: GFS
      type: accumulate
      data_dir: {data_dir}
      data_pattern: '{data_pattern}'
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'
      number_of_days: {accumulate_days}
      dates: [{year}-{month}-{day}]
      """.format(accumulate_days=accumulate_days, data_dir=data_dir, data_pattern=data_pattern,
                 output_dir=output_dir, output_pattern=output_pattern, year=self.product_date.strftime("%Y"),
                 month=self.product_date.strftime("%m"), day=self.product_date.strftime("%d"))
        return config