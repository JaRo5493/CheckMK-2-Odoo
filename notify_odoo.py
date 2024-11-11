#!/usr/bin/env python3
# Odoo Helpdesk API Connection
#
# Script Name   : notify_odoo.py
# Description   : Send Check_MK notifications to Odoo and manage Tickets.
# Author        : JR

import os
import xmlrpc.client
import logging

# Configure logging
logging.basicConfig(filename='/tmp/checkmk_odoo_notification.log', level=logging.DEBUG)


def log_info(message):
    logging.info(message)


def log_debug(message):
    logging.debug(message)


def log_error(message):
    logging.error(message)


# Parameters from CheckMK for Odoo connection:
url = os.getenv('NOTIFY_PARAMETER_1')
db = os.getenv('NOTIFY_PARAMETER_2')
uid = os.getenv('NOTIFY_PARAMETER_3')
api_key = os.getenv('NOTIFY_PARAMETER_4')

# Retrieve the environment variable for processing.
customer = os.getenv('NOTIFY_HOST_CUSTOMER')
site = os.getenv('OMD_SITE')
what = os.getenv('NOTIFY_WHAT')
notification_type = os.getenv('NOTIFY_NOTIFICATIONTYPE')

host_name = os.getenv('NOTIFY_HOSTNAME')
service_name = os.getenv('NOTIFY_SERVICEDISPLAYNAME')

output_host = os.getenv('NOTIFY_HOSTOUTPUT')
output_service = os.getenv('NOTIFY_SERVICEOUTPUT')

host_state = os.getenv('NOTIFY_HOSTSTATE')
service_state = os.getenv('NOTIFY_SERVICESTATE')

host_problem_id = os.getenv('NOTIFY_HOSTPROBLEMID')
service_problem_id = os.getenv('NOTIFY_SERVICEPROBLEMID')

last_host_problem_id = os.getenv('NOTIFY_LASTHOSTPROBLEMID')
last_service_problem_id = os.getenv('NOTIFY_LASTSERVICEPROBLEMID')


# Connect to Odoo
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))


def create_ticket(customer_identifier,checkmk_site, type, checkmk_hostname, checkmk_id, checkmk_problem, checkmk_service_name = None):
    log_debug(f"Creating ticket for {customer_identifier}")
    try:
        ticket = {
            'description': checkmk_problem,
            'partner_id': customer_identifier,
            'area_id': 1,
            'team_id': 5,
            'ticket_type_id': 6,
            'put_off_email': True,
            'x_CHECKMK_HOSTNAME': checkmk_hostname,
            'x_CHECKMK_PROBLEM_ID': checkmk_id
        }
        # Check for Host or Service Type and Set Ticket Name accordingly.
        if type == 'HOST':
            ticket['name'] = f'Ticket for {checkmk_site} - Host: {checkmk_hostname}'
        elif type == 'SERVICE':
            ticket['name'] = f'Ticket for {checkmk_site} - Host: {checkmk_hostname} - Service: {checkmk_service_name}'

        # Check for Service Name and add it to the ticket.
        if checkmk_service_name is not None:
            ticket['x_CHECKMK_SERVICE_NAME'] = checkmk_service_name
        # Create Ticket with all Fields
        ticket_id = models.execute_kw(db, uid, api_key, 'helpdesk.ticket', 'create', [ticket])
        return ticket_id
    except Exception as e:
        log_error(f"Error creating ticket: {str(e)}")
        log_debug(f"Customer ID: {customer_identifier} - Site: {checkmk_site} - Type: {type} - Host: {checkmk_hostname} "
                  f"- ID: {checkmk_id} - Problem: {checkmk_problem} - Service: {checkmk_service_name}")
        return None


def update_ticket(ticket_id, new_description):
    log_debug(f"Updating ticket {ticket_id}")
    try:
        models.execute_kw(db, uid, api_key, 'helpdesk.ticket', 'write', [[ticket_id], {
            'description': new_description
        }])
    except Exception as e:
        log_error(f"Error updating ticket: {str(e)}")


def close_ticket(ticket_id):
    log_debug(f"Closing ticket {ticket_id}")
    try:
        models.execute_kw(db, uid, api_key, 'helpdesk.ticket', 'write', [[ticket_id], {
            'stage_id': 69
        }])
    except Exception as e:
        log_error(f"Error closing ticket: {str(e)}")


def find_existing_ticket(customer_identifier,checkmk_hostname, checkmk_id, checkmk_service_name = None):
    try:
        search_domain = [
            ['area_id', '=', 1],
            ['team_id', '=', 5],
            ['stage_id', '!=', 68],
            ['x_CHECKMK_HOSTNAME', '=', checkmk_hostname],
            ['x_CHECKMK_PROBLEM_ID', '=', checkmk_id]
        ]

        if customer_identifier != 0:
            search_domain.append(['partner_id', '=', customer_identifier])

        # Check for Service Name and add it to the ticket.
        if checkmk_service_name is not None:
            search_domain.append(['x_CHECKMK_SERVICE_NAME', '=', checkmk_service_name])

        # Search for an open ticket for the customer
        ticket_ids = models.execute_kw(db, uid, api_key, 'helpdesk.ticket', 'search', [search_domain])
        log_info(f"Existing Ticket found: ID {ticket_ids[0]}")
        return ticket_ids[0] if ticket_ids else None
    except Exception as e:
        log_debug(
            f"135: Customer ID: {customer_identifier} - Host: {checkmk_hostname} - ID: {checkmk_id} - Service: {checkmk_service_name}")
        return None


def check_customer_identifier(customer_id_raw):
    if customer_id_raw:
        customer_id_filtered = customer_id_raw.split('_')[-1]
        try:
            new_value = int(customer_id_filtered)
            return new_value
        except ValueError:
            log_error("Customer ID is not correctly set in CheckMK.")
            return 0
    else:
        log_debug("Environment variable NOTIFY_HOST_CUSTOMER is not set")
        return 0


def main():
    try:
        # Check for Customer ID otherwise use 0.
        customer_identifier = check_customer_identifier(customer)

        # Set Problem ID and Description based on Host or Service.
        problem_id = 0
        problem_description = ''
        if what == 'HOST':
            if host_problem_id == '0':
                problem_id = int(last_host_problem_id)
            else:
                problem_id = int(host_problem_id)
            problem_description = output_host
        elif what == 'SERVICE':
            if service_problem_id == '0':
                problem_id = int(last_service_problem_id)
            else:
                problem_id = int(service_problem_id)
            problem_description = output_service

        # Check the notification type and react accordingly.
        log_debug(f"166: Notification Type: {notification_type} - Host: {host_name} - what: {what} - ID: {problem_id}")
        if notification_type == 'PROBLEM':
            ticket_id = find_existing_ticket(customer_identifier, host_name, problem_id, service_name)
            if ticket_id:
                #update_ticket(ticket_id, description)
                log_debug(f"180: Ticket already exists for {customer_identifier}")
            else:
                log_debug(f"182: Create Ticket for {site} - Host: {host_name} State: {host_state} ID: {problem_id} Problem: {output_host}")
                create_ticket(customer_identifier, site, what, host_name, problem_id, problem_description, service_name)
        elif notification_type == 'RECOVERY':
            log_debug(
                f"186: Close Ticket for {site} - Host: {host_name} State: {host_state} ID: {problem_id} Problem: {output_host}")
            ticket_id = find_existing_ticket(customer_identifier, host_name, problem_id, service_name)
            if ticket_id:
                close_ticket(ticket_id)
    except Exception as e:
        log_error(f"Script failed: {str(e)}")


if __name__ == "__main__":
    main()
