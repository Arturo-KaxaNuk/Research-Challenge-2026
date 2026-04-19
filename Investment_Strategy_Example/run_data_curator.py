"""
Entry script that reads Data Curator configuration from an Excel file, registers custom
calculation modules, and outputs enriched datasets to csv and parquet files.

Environment Variables
---------------------
KNDC_API_KEY_FMP
    API key for the Financial Modeling Prep data provider.
KNDC_API_KEY_LSEG
    API key for the LSEG Workspace data provider.
"""

import os
import pathlib

import kaxanuk.data_curator


# Load the user's environment variables from Config/.env, including data provider API keys
kaxanuk.data_curator.load_config_env()

# Load user's custom calculations module, if exists in Config dir
if (pathlib.Path('src/data_curator/alpha_signals/simple_moving_average_alpha_signal.py').is_file()
    and pathlib.Path('src/data_curator/market/missing_market_data.py').is_file()
    and pathlib.Path('src/data_curator/outlier_adjusted_data/shares_outstanding_outlier_adjusted.py').is_file()
):
    # noinspection PyUnresolvedReferences
    from data_curator.alpha_signals import simple_moving_average_alpha_signal
    from data_curator.market import missing_market_data
    from data_curator.outlier_adjusted_data import shares_outstanding_outlier_adjusted

    custom_calculation_modules = [simple_moving_average_alpha_signal,
                                  missing_market_data,
                                  shares_outstanding_outlier_adjusted,
                                  ]
else:
    custom_calculation_modules = []

output_base_dir = 'Data_Curator'

# Load the configuration from the file
parameters_excel_file = 'Config/data_curator_parameters.xlsx'
configurator = kaxanuk.data_curator.config_handlers.ExcelConfigurator(
    file_path=parameters_excel_file,
    data_providers={
        'financial_modeling_prep': {
            'class': kaxanuk.data_curator.data_providers.FinancialModelingPrep,
            'api_key': os.getenv('KNDC_API_KEY_FMP'),   # set this up in the Config/.env file
        },
        'lseg_workspace': {
            'class': kaxanuk.data_curator.data_providers.LsegWorkspace,
            'api_key': os.getenv('KNDC_API_KEY_LSEG'), # set this up in the Config/.env file
        },
        'yahoo_finance': {
            'class': kaxanuk.data_curator.load_data_provider_extension(
                extension_name='yahoo_finance',
                extension_class_name='YahooFinance',
            ),
            'api_key': None     # this provider doesn't use API key
        },
    },
    output_handlers={
        'csv': kaxanuk.data_curator.output_handlers.CsvOutput(
            output_base_dir=output_base_dir,
        ),
        'parquet': kaxanuk.data_curator.output_handlers.ParquetOutput(
            output_base_dir=output_base_dir,
        ),
    },
)

# Run this puppy!
kaxanuk.data_curator.main(
    configuration=configurator.get_configuration(),
    market_data_provider=configurator.get_market_data_provider(),
    fundamental_data_provider=configurator.get_fundamental_data_provider(),
    output_handlers=[configurator.get_output_handler()],
    custom_calculation_modules=custom_calculation_modules,  # Optional
    logger_level=configurator.get_logger_level(),           # Optional
)
