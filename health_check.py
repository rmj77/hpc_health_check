#!/usr/bin/env python3

import check.default as default_check
import config.args as args_config
import config.connection.connection as connection_config
import config.file as config_file
import config.parser as config_parser
import connection.local.local as local_connection
import connection.ssh.ssh as ssh_connection
import connection.ssh.totp.totp as ssh_totp_connection
import copy
import dicttoxml
import error.command as command_error
import json
import logging
import tests.test as test
import yaml


def main():
    args = args_config.get_configuration()
    if args.command == "test":
        # The following line calls sys.exit on completion (whether successful or not)  # noqa: E501
        test.run_tests()
    checks = []
    connections = []
    if args.command == "file":
        config_dict = config_file.get_config(args.filename)
        checks = config_dict["checks"]
        connections = [
            item["type"](item["config"]) for item
            in config_dict["connections"]
        ]
    else:
        if args.command == "local":
            connections.append(
                local_connection.LocalConnection(
                    connection_config.LocalConnectionConfiguration()
                )
            )
        elif args.command == "ssh":
            conn = None
            config = connection_config.SSHConnectionConfiguration(
                args.username,
                args.password,
                args.address
            )
            if args.port:
                config.port = args.port
            if args.totp_seed:
                config.totp_seed = args.totp_seed
            if args.totp_seed:
                conn = ssh_totp_connection.SSHTotpConnection(config)
            else:
                conn = ssh_connection.SSHConnection(config)
            connections.append(conn)

        all_args = "all" in args.check
        for check_dict in default_check.get_default_checks():
            if all_args or check_dict['name'] in args.check:
                checks.append(check_dict)
    check_results = []
    globbed_connections = []
    for conn in connections:
        if isinstance(
            conn, ssh_connection.SSHConnection
        ) and not config_parser.is_address_string_expanded(
            conn.configuration.address
        ):
            globbed_addresses = config_parser.expand_address_string(
                conn.configuration.address
            )
            for address in globbed_addresses:
                new_connection = copy.deepcopy(conn)
                new_connection.configuration.address = address
                globbed_connections.append(new_connection)
        else:
            globbed_connections.append(conn)
    connections = globbed_connections
    for conn in connections:
        conn.connect()
    for check in checks:
        for conn in connections:
            check_inst = check["check"](check["config"], conn)
            try:
                logging.info("Running check {}".format(check["name"]))
                check_inst.run()
                check_results.append({
                    "name": check["name"],
                    "result": check_inst.result,
                    "connection": conn.get_runtime_meta(),
                })
            except command_error.CommandNotFoundError:
                check_results.append({
                    "name": check["name"],
                    "result": {"error": "Command not found"},
                    "connection": conn.get_runtime_meta(),
                })
            except NotImplementedError:
                check_results.append({
                    "name": check["name"],
                    "result": {"error": "Check not fully implemented"},
                    "connection": conn.get_runtime_meta(),
                })
    for conn in connections:
        conn.close()
    if len(check_results):
        check_results = {"results": check_results}
        if args.out == "json":
            print(json.dumps(check_results))
        elif args.out == "yaml":
            print(yaml.dump(check_results))
        elif args.out == "xml":
            print(dicttoxml.dicttoxml(check_results))


if __name__ == "__main__":
    main()
