"""
Entry script that reads backtest configuration from an Excel file, wires up
market-data and portfolio input handlers, and runs the KaxaNuk backtest engine.

Environment Variables
---------------------
KAXANUK_LICENSE_KEY
    License key required by the backtest engine (loaded from Config/.env).
APPENV
    Set to 'dev' to enable PyCharm remote debugger attachment.
DEBUG_PORT
    Port number for the PyCharm debugger (only used when APPENV == 'dev').
"""

import os

from kaxanuk.backtest_engine.modules import debugger
from kaxanuk.backtest_engine.services.env_loader import load_config_env
import kaxanuk.backtest_engine.backtest_engine


load_config_env()

if os.environ.get('APPENV') == 'dev':
    debugger.init(
        int(os.environ.get('DEBUG_PORT'))
    )


configurator = kaxanuk.backtest_engine.config_handlers.excel_configurator.ExcelConfigurator(
    file_path='Config/backtest_engine_parameters.xlsx'
)

configuration = configurator.get_configuration()

market_data_input_handlers = {
    'csv': kaxanuk.backtest_engine.input_handlers.csv_input.CsvInput(
        input_dir=configuration.input_market_data_directory
    ),
    'parquet': kaxanuk.backtest_engine.input_handlers.parquet_input.ParquetInput(
        input_dir=configuration.input_market_data_directory
    ),
}

portfolio_input_handlers = {
    'csv': kaxanuk.backtest_engine.input_handlers.csv_portfolio_input_handler.CsvPortfolioInputHandler(  # noqa: E501
        base_dir=configuration.input_portfolio_directory
    ),
    'excel': kaxanuk.backtest_engine.input_handlers.excel_portfolio_input_handler.ExcelPortfolioInputHandler(  # noqa: E501
        base_dir=configuration.input_portfolio_directory
    ),
}

market_data_input_handler = market_data_input_handlers[configuration.market_data_input_format]
portfolio_input_handler = portfolio_input_handlers[configuration.portfolio_input_format]

register = kaxanuk.backtest_engine.backtest_engine.main(
    configuration=configuration,
    input_handlers=[market_data_input_handler],
    portfolio_handlers=[portfolio_input_handler],
    logger_level=configurator.get_logger_level(),
    dashboard_port=configurator.get_dashboard_port(),
    launch_dashboard=True,
    logger_file=None,
)
