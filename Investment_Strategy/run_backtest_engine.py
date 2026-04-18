import os

from kaxanuk.backtest_engine.modules import debugger
from kaxanuk.backtest_engine.services.env_loader import load_config_env
import kaxanuk.backtest_engine.backtest_engine

# Load Config/.env so KAXANUK_LICENSE_KEY (and any other env vars) are available
load_config_env()

# Initialize Pycharm debug if we're on dev environment
if os.environ.get('APPENV') == 'dev':

    debugger.init(
        int(os.environ.get('DEBUG_PORT'))
    )


# Load the configuration from the file
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
        'csv': kaxanuk.backtest_engine.input_handlers.csv_portfolio_input_handler.CsvPortfolioInputHandler(
            base_dir=configuration.input_portfolio_directory
        ),
        'excel': kaxanuk.backtest_engine.input_handlers.excel_portfolio_input_handler.ExcelPortfolioInputHandler(
            base_dir=configuration.input_portfolio_directory
        )
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
