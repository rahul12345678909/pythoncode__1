#!/usr/bin/python3

import subprocess
import os
import time
import xml.etree.ElementTree as ET

def transform_result_name(result_name):
    transformed_name = result_name.replace('/', '')
    return transformed_name

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
    result_txt_path = f"/tests/jenkins/pts/workspace/guest_regression/{transformed_result_name}/extracted_result.txt"

    start_time = time.time()
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # Prepare responses to be passed to PTS
    responses = [
        "4",  # Processor Test Configuration: 7 (Test All Options)
        "Y",  # Would you like to save these test results? (Y/n): Y
        transformed_result_name,  # Enter a name for the result file
        f"Test run for {test_name} on kernel {kernel_version}",  # Enter a unique name to describe this test run / configuration
        "Automated test run for pts/nginx on this system.",  # New Description
        "n",  # Would you like to view the results in your web browser (Y/n): n
        "n"   # Would you like to upload the results to OpenBenchmarking.org (y/n): n
    ]

    process = subprocess.Popen(
        ['phoronix-test-suite', 'benchmark', test_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    try:
        for response in responses:
            print(f"Sending response: {response}")
            process.stdin.write(response + '\n')
            process.stdin.flush()
            time.sleep(5)  # Adjust as necessary to match the prompts timing

        stdout, stderr = process.communicate(timeout=2400)  # Wait up to 10 minutes for completion

        # print(f"stdout:\n{stdout}")
        # print(f"stderr:\n{stderr}")

    except subprocess.TimeoutExpired:
        print("Phoronix Test Suite process took too long to complete and was terminated.")
        process.kill()
        stdout, stderr = process.communicate()
        print(f"stdout:\n{stdout}")
        print(f"stderr:\n{stderr}")

    except Exception as e:
        print(f"An error occurred: {e}")
        process.kill()
        stdout, stderr = process.communicate()
        print(f"stdout:\n{stdout}")
        print(f"stderr:\n{stderr}")

    finally:
        end_time = time.time()
        print(f"Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        print(f"Duration: {end_time - start_time:.2f} seconds")

        # Extract results and save to a text file
        extract_results(result_xml_path, result_txt_path)

if __name__ == "__main__":
    test_name = "pts/nginx"
    run_phoronix_test(test_name)
