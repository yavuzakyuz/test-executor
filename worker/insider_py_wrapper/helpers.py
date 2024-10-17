from colorama import init, Fore, Style

init(autoreset=True)

def run_test(description, test_function):
    try:
        print(Fore.CYAN + f"--- Starting: {description} ---")
        test_function()  # do the test
        print(Fore.GREEN + f"--- {description}: Passed ---")
    except AssertionError as e:
        print(Fore.RED + f"--- {description}: Failed - {str(e)} ---")
    except Exception as e:
        print(Fore.RED + f"--- {description}: Encountered an Error - {str(e)} ---")
    finally:
        print(Fore.CYAN + f"--- Moving to the next test ---\n") # unless it's the last test, I can add that case later on 