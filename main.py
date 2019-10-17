import datetime
import configparser
import argparse
import logging

from jinja2 import Environment, PackageLoader, select_autoescape
from prompt_toolkit.key_binding.bindings.named_commands import end_of_file

from review_generator.victoropsapi import VictorOpsAPI
from review_generator.analizer import IncidentAnalizer


def arg_parse():
    """
    Creates/sets up argparser instance
    """
    parser = argparse.ArgumentParser(description="""VictorOps statistics generator.""",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-c', '--config', dest='config_file', help='Configuration file', default='config.ini')

    parser.add_argument('-s', '--start_date', dest='start_date', help='Period start date in format DD.MM.YYYY')
    parser.add_argument('-e', '--end_date', dest='end_date', help='Period end date in format DD.MM.YYYY')

    #                     default="%s.aws\\" % home)
    # parser.add_argument('-u', '--user', dest='db_user', help='Database user')


    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-d", "--debug", dest='debug', action="store_true",
                       help='Debug mode (includes verbose mode)', default=False)
    group.add_argument('-v', '--verbose', dest='verbose', action="store_true",
                       help='Verbose mode', default=False)

    return parser.parse_args()


def get_logger(args):
    FORMAT = '%(asctime)s\t%(levelname)s\t%(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger()

    logger.setLevel(logging.WARNING)
    if args.verbose:
        logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.debug("Args: %s", repr(args))
    return logger


def parse_sdate(string_date):
    return datetime.datetime.strptime(string_date, "%d.%m.%Y").date()


def main():
    # arguments
    args = arg_parse()

    # logging
    logger = get_logger(args)


    env = Environment(
        loader=PackageLoader("review_generator", 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # configuration
    config = configparser.ConfigParser()
    config.read(args.config_file)

    template = env.get_template(config["Generator"]["template"])

    # Victor
    victor_ops_api = VictorOpsAPI(config['VictorOps']['APP_ID'], config['VictorOps']['API_KEY'])

    # Analizer
    analizer = IncidentAnalizer(int(config['WorkTime']['start']), int(config['WorkTime']['end']),
                                config['WorkTime']['holidays'])


    # get incidents
    start_date = datetime.datetime.strptime('21.08.2019', "%d.%m.%Y").date() # provide as parameter
    end_date =  datetime.datetime.strptime('04.09.2019', "%d.%m.%Y").date() # provide as parameter

    try:
        if args.start_date:
            start_date = parse_sdate(args.start_date)
        else:
            start_date = parse_sdate(config['Period']['start_date'])
    except ValueError as e:
        logger.error("Incorrect start date. Provide date in format DD.MM.YYYY as parameter -s|--start_date")
    try:
        if args.end_date:
            end_date = parse_sdate(args.end_date)
        else:
            end_date = parse_sdate(config['Period']['end_date'])
    except ValueError as e:
        logger.error("Incorrect end date. Provide date in format DD.MM.YYYY as parameter -e|--end_date")

    logger.debug(victor_ops_api)
    logger.info("Period: %s -> %s", start_date, end_date)

    incidents = victor_ops_api.get_incidents(config["VictorOps"]["ROUTING_KEY"], start_date, end_date)

    # Analise
    analizer.set_kpis(incidents)
    statistical_analysis = analizer.get_statistical_analysis(incidents)

    logger.debug(repr(incidents))
    output = template.render(vo_client_name=config["VictorOps"]["CLIENT_NAME"], incidents=incidents, statistical_analysis=statistical_analysis)

    with open(config["Generator"]["output_file"], "w") as file:
        file.write(output)

    logger.debug("\n%s\n", output)


if __name__ == '__main__':
    main();