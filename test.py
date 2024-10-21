#!/usr/bin/python3

import pexpect
import re
import os
import time
import xml.etree.ElementTree as ET


def create_unique_run_type(run_type):
    """
    Create a new unique run type using current timestamp.

    :param run_type: Run type
    :return: str
    """
    from time import localtime, strftime
    current_time = strftime("%H_%M_%S", localtime())
    get_current_date = strftime("%d_%m_%Y", localtime())
    date_and_time = get_current_date + '_' + current_time
    pid = str(os.getpid())
    run_type_stamp = os.path.normpath(date_and_time + '_' + pid + '_' + run_type)
    return run_type_stamp


def transform_result_name(result_name):
    # Remove any slashes from the result name
    transformed_name = result_name.replace('/', '')
    unique_transformed_name = create_unique_run_type(transformed_name)
    return unique_transformed_name.replace('_', '-')


def extract_results(xml_path, txt_path):
    if not os.path.isfile(xml_path):
        print(f"File {xml_path} does not exist.")
        return

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        with open(txt_path, 'w') as file:
            for result in root.findall('.//Result'):
                title = result.find('Title').text if result.find('Title') is not None else 'N/A'
                description = result.find('Description').text if result.find('Description') is not None else 'N/A'
                scale = result.find('Scale').text if result.find('Scale') is not None else 'N/A'
                value = result.find('.//Value').text if result.find('.//Value') is not None else 'N/A'
                file.write(f"Title: {title}\n")
                file.write(f"Description: {description}\n")
                file.write(f"Scale: {scale}\n")
                file.write(f"Value: {value}\n")
                file.write('-' * 40 + '\n')
        print(f"Results saved to {txt_path}")
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")




def run_phoronix_test(test_name):
    kernel_version = os.uname().release
    result_name = f"{test_name}"
    transformed_result_name = transform_result_name(result_name)
    print(f"transformed_result_name: {transformed_result_name}")
    result_xml_path = f"/home/amd/.phoronix-test-suite/test-results/{transformed_result_name}/composite.xml"
    result_txt_path = f"/home/amd/.phoronix-test-suite/test-results/{transformed_result_name}/{transformed_result_name}_result.txt"
    start_time = time.time()
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # Start the Phoronix Test Suite process
    child = pexpect.spawn('phoronix-test-suite benchmark pts/nginx', timeout=540)
    unique_log = create_unique_run_type("Ngx7_output.log")
    child.logfile = open(unique_log, "wb")

    try:
        unique_test_name = create_unique_run_type(test_name)
        # List of prompts and responses
        prompts_and_responses = [
            (r"System Test Configuration", None),
            (r"Connections:.*", "2"),
            (r"Would you like to save these test results \(Y/n\):".encode(), "y"),
            (r"Enter a name for the result file:".encode(), transformed_result_name),
            (r"Enter a unique name to describe this test run / configuration:".encode(), f"Test run for {unique_test_name} on kernel {kernel_version}"),
            (r"New Description:".encode(), "Automated test run for pts/nginx on this system."),
            (re.compile(r"Do you want to view the results in your web browser \(Y/n\)\:".encode()), "n"),
            (re.compile(r"Would you like to upload the results to OpenBenchmarking\.org \(y/n\)\:".encode()), "n")
        ]

        # Loop through the prompts and send the corresponding responses
        for prompt, response in prompts_and_responses:
            child.expect(prompt)
            if response is not None:
                child.sendline(response)

        # Ensuring the test completes and the results file is generated
        child.expect(pexpect.EOF)

        # Checking if the results file exists
        if not os.path.exists(result_xml_path):
            print(f"File {result_xml_path} does not exist.")
        else:
            print(f"File {result_xml_path} exists.")
            extract_results(result_xml_path, result_txt_path)

    except pexpect.TIMEOUT:
        print("Timeout error: Timeout exceeded.")
    except pexpect.ExceptionPexpect as e:
        print(f"An error occurred: {e}")
    finally:
        child.logfile.close()
        end_time = time.time()
        print(f"Test ended at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

if __name__ == "__main__":
    run_phoronix_test("pts/nginx")
