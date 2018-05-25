#!/usr/bin/env: python3

""" 
A user interaction based python script that analyzes a USAA bank statement. There
are plans to add visual representations of how money is spent and ultimately 
compare the new bank statement to past statements. 

This script has some drawbacks:
    - If a refund is credited back using the same name, it might get marked
    as a deposit and a debit with some weird side effects.
    - Classifying transactions is a little crude: I would like to allow the 
    user to get more information about at transaction if they'd like. This 
    can probably be fixed by representing data differently.

"""


#
# TODO: If a refund is received, there's no differentiation between
#       the purchase and the refund. Maybe getting transaction type
#       is useful.
#
#       Need to make a decision on how to store transactions -- grouping
#       by transaction or keeping them all separate. Grouping them 
#       assumes that each transaction is the same class. What if one
#       transaction is a red bull bought at a gas station and another
#       transaction is gas bought at the same gas station? Red bulls
#       and gas should be differntiated. Right now, they're lumped
#       into the same category, and as a result, the analysis is imprecise.
#
#       Conform to PEP8
#


import re
import os.path
import argparse


class Transaction:
    def __init__(self, name, transaction_type, transaction_list):
        self.name = name
        self.transaction_type = transaction_type
        self.transaction_dates = []
        self.transaction_total = 0

        self.transaction_list = []
        self.transaction_list.append(transaction_list)

    def __str__(self):
        return self.name + ": " + self.transaction_type + ", " + str(self.transaction_list)

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        
        return self.name == other.name and self.transaction_type == other.transaction_type
        
    def get_transaction_total(self):
        total = 0
        
        for t in self.transaction_list:
            total += t[1]
        
        return total


class USAAnalyzer:
    _classifiers = ['Deposit', 'Savings', 'Misc', 'Bill', 'Grocery', 'Fuel', 'Restaurant', 'Coffee']
    _portions = {} 
    _transactions = []
    _num_transactions = 0

    def __init__(self, file_name):
        # Open file for reading
        with open(file_name, "r") as f:
            line = f.readline()

            # Skip information I don't know how to handle yet. In the future,
            # I'd like to use this information to validate file parsing.
            while line:
                if line == 'DEPOSITS AND OTHER CREDITS\n':
                    break
                line = f.readline()
           

            # Build a list of transactions. This function will populate
            # self._transactions
            self._get_transactions(f)

        # Condense the list to make it more succinct. Similar to 
        # self._get_transactions(), this function will store the result in
        # self._transactions.
        self._condense_transactions()

        # Retrieve a list of collectors if it exists. Add unknown ones 
        # if necessary. If collectors file doesn't exist, read from file.
        # Otherwise, no list of collectors in working directory. Build 
        # one from list of deposits and debits and write contents to file.
        if os.path.isfile('.collectors'): 
            print('---Found collectors file---')
            self._read_collector_file()
        else:
            print("---Collectors file not found, performing setup---")
            self._write_collector_file()

        # TODO: classify transactions, print results in a meaningful way.
        #       I'd like to eventually use a graphics library to show a chart.

    #
    # Overriden __str__. Provides a high-level view of analysis done on
    # bank statement.
    #
    def __str__(self):
        # Get portions so we can provide a meaningful analysis
        deposit_total, debit_total = self._get_portions()
        
        val_total = 0.0
        result = ""
        open_string = "{}:\n{:10.2f} -- {:.2%}"

        result = ""

        # Enumerate over dictionary of portions so we can find percent of
        # money spent on each transaction class.
        for k, v in self._portions.items(): 
            val = 0.0

            if k == "Deposit":
                val = v / deposit_total
            else:
                val = v / debit_total
                val_total += val

            result += "\n" + open_string.format(k, v, val)

        return result

    #
    # Parses an input file until a specified stop point. Uses a regular
    # expression to match a money line. Handles the special case for 
    # USAA internal transactions and generic transactions given the
    # file comes from USAA.
    #
    def _get_transactions(self, f):
        date_pattern = re.compile('\d+\/\d+')
        star_pattern = re.compile('^\*')

        transaction_type = 'Deposit'
        
        line = f.readline()
        while line:
            
            # Break at next section
            if line == 'OTHER DEBITS\n':
                transaction_type = 'Debit'

            # Each transaction is preceeded by a date. If we find another date while
            # parsing transaction info, we have reached another transaction.
            if date_pattern.match(line):
                date = line.replace('\n', '')
                line = f.readline()
                temp = []
                
                # 6 was chosen on a hueristic basis. I basically check the 'length'
                # of transaction details and determined that 6 was the maximum.
                for i in range(6):
                    if date_pattern.match(line) or line == 'OTHER DEBITS\n':
                        break
                    else:
                        temp.append(line)
                        line = f.readline()

                money_line = temp[0]
                money_line_tokens = money_line.split(' ')
                money = float(money_line_tokens[0].replace(',', '')) # remove commas
                
                # Generally, line 1 contains amount and type, line 2 is when 
                # transaction cleared, line 3 is where money is going or coming 
                # from. Some transaction details are shorter so we will handle 
                # those cases.
                collector = 'DEFAULT'
                if len(temp) >= 4:
                    if star_pattern.match(temp[3]):
                        name = temp[2]
                    else:
                        name = temp[3]
                elif len(temp) == 2:
                    name = temp[1]
                elif len(temp) < 2:
                    name = ' '.join(money_line_tokens[1:])

                # Create new transaction with this information
                transaction = Transaction(name.strip(), transaction_type, [date, money])
                self._transactions.append(transaction)

            # If we've gotten this far, we've reached the summary part of the
            # bank statement so we can stop.
            elif line == 'DATE..........BALANCE\n':
                break
            
            else:
                line = f.readline()

        self._num_transactions = len(self._transactions)

    #
    # Group transactions by transaction name in order to make list
    # more concise. This function will overwrite the original transaction
    # list with the condensed version.
    #
    def _condense_transactions(self):
        new_transaction_list = []

        # Iterate transaction list and condense transactions
        for current in self._transactions:
            # If the transaction is not already in the list, add it to the list
            if current not in new_transaction_list:
                new_transaction_list.append(current)

            # Otherwise, we need to find the matching name and add dates/money
            else:
                for t in new_transaction_list:
                    if t == current:
                        t.transaction_list.append(current.transaction_list.pop())

        self._transactions = new_transaction_list

    #
    # Builds a list of money spent on classifcation type. Returns the deposit 
    # total and debit total. This function will overwite self._portions.
    #
    def _get_portions(self):
        classifier_portions = {} 
        debit_total, deposit_total = 0.0, 0.0

        # Prefill classifiers with known class types and initial money value. 
        # Class types are retrieved from the value position in the dictionary.
        for c in self._classifiers:
            classifier_portions[c] = 0.0
        
        # Get total value for each type of transaction
        for t in self._transactions:
            classifier_portions[t.transaction_type] += t.get_transaction_total() 

        # Reassign portions
        self._portions = classifier_portions
       
        # Get totals for deposits and debits
        for k, v in classifier_portions.items():
            if k == 'Deposit':
                deposit_total += v
            else:
                debit_total += v
        
        return deposit_total, debit_total 

    #
    # Builds a file of collectors and class types. This file is stored
    # in the working directory and should be appended to when new 
    # collectors are found.
    #
    def _write_collector_file(self):
        with open('.collectors', 'w') as f:
           
            # Iterate transactions and assign transaction type. Append type to
            # classifiers if necessary and write to file.
            for t in self._transactions:
                transaction_type = self._get_collector_input(t)
                if transaction_type not in self._classifiers:
                    self._classifiers.append(transaction_type)
                
                t.transaction_type = transaction_type
                f.write(t.name + ', ' + transaction_type + '\n')

    #
    # Helper function for build collectors. Prompts user for what kind of 
    # classification should be applied to a collector and returns approved
    # classification type. I would ultimately like to expand the user 
    # interaction with this function: if the user doesn't recognize what
    # the transaction is, print the most recent transaction with money spent
    # and date. I want to avoid using the OOP with this project so I will
    # side with a simpler approach.
    #
    # TODO: Allow user to itemize transaction events. I believe this will
    #       minimize chances for unnecessary grouping, i.e. buying redbull
    #       and gas at a gas station.
    #
    def _get_collector_input(self, transaction):
        answer = '???'
        open_string = '{} {:10.2f}'

        # Emulate apt-get package manager style validation. Yes is 
        # default so allows user to type Y, y or press enter. Any
        # other input is treated as a "no". Iterate until user is
        # satisfied with transaction type.
        while answer != "" and answer != "y" and answer != "Y":

            k = None
            transaction_type = 'DEFAULT'

            # Show user menu
            print('')
            for i in range(len(self._classifiers)):
                print("\t" + str(i+1) + ". " + self._classifiers[i])
            print('\t0. Other\n')

            # Get user input
            while k is None:
                print('Transaction name:', transaction.name)
                k = input('Please enter numeric transaction type or "d" for transaction details: ')
                   
                # Show user transaction details if necessary. This will show
                # dates and amount spent on that date.
                if k == 'd':
                    print('\n"', transaction.name, '" transaction details:') 
                    print('\tDate      Amount')

                    for event in transaction.transaction_list:
                        print("\t" + open_string.format(event[0], event[1]))
                    
                    print('')
                    k = None
                
                else:
                    # Attempt to cast input to integer so we can index menu
                    try:
                        k = int(k)
                        
                        # Catch invalid input and prompt again if necessary
                        if (k < 0 or k > len(self._classifiers)):
                            print('\n\t*Invalid input, try again*\n')
                            k = None
                        
                        # If input is good, assign transaction type 
                        else:
                            transaction_type = self._classifiers[k-1]

                    # Handle invalid input gracefully
                    except ValueError or TypeError:
                        print('\n*\tInvalid input, try again*\n')
                        k = None

            # Allow user to enter new transaction type
            if k == 0:
                transaction_type = input('Please enter new type: ')
           
            # Get user confirmation for transaction type
            answer = input("Set " + transaction.name + " as " + transaction_type + " [Y]\\n?: ")

        print('')
        return transaction_type

    #
    # Builds a list of collectors from a file. Parses current list of deposits and
    # debits to add new collectors if necessary.
    #
    def _read_collector_file(self):
        # Build list of collectors from file
        with open(".collectors", "r") as f:
            line = f.readline()

            # Split lines by comma. LHS is transaction name, RHS is type.
            while line:
                tokens = line.split(", ")
                transaction_type = tokens[1].strip()
                
                # Add the type if it is not already in classifiers
                if transaction_type not in self._classifiers:
                    self._classifiers.append(transaction_type)
               
                # Update transaction with appropriate type
                for t in self._transactions:
                    if t.name == tokens[0]:
                        t.transaction_type = transaction_type

                line = f.readline()

        # TODO
        # Append to an existing file containing collectors
#        with open(".collectors", "a") as f:
#            # for transaction in self._deposits:
#            #     # If the collector isn't found in the list of collectors,
#            #     # prompt user for collector type and append to file. I can
#            #     # skip collector input for deposits since they are all the
#            #     # same class.
#            #     if not self._has_collector(transaction[0]):
#            #         print("--- Adding new deposits ---")
#            #         self._collectors.append([transaction[0], "deposit"])
#            #         f.write(transaction[0].strip() + " , deposit\n")
#
#            # for transaction in self._debits:
#            #     if not self._has_collector(transaction[0]):
#            #         print("--- Found new debit ---")
#            #         collector_type = self._get_collector_input(transaction)
#            #         self._collectors.append([transaction[0], collector_type])
#            #         f.write(transaction[0].strip() + ", " + collector_type + "\n")
#            for t in self._transactions:
#                # If the collector isn't found in the list of collectors,
#                # prompt user for collector type and append to file.
#                if not self._has_collector(t.name):
#                    print("--- Adding new transactions ---")
#                    self._collectors.append([t.name, t.transaction_type])
#                    f.write(t.name + ", " + t.transaction_type + "\n")      

    def len(self):
        return self._num_transactions


# TODO: Provide user with more controls over collector file
def main():
    # Handle args 
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="name of raw USAA bank statement to be analyzed")
    args = parser.parse_args()
    
    # If arg file is valid, continue
    if os.path.isfile(args.file_name) is not None:
        file_name = args.file_name
       
        # Python cannot read pdf encoding but we want to accept pdf's as input
        # so convert to text file if needed.
        if file_name.endswith('.pdf'):
            os.system('pdftotext '+file_name)    
            file_name = file_name.replace('.pdf', '.txt')

        analyzer = USAAnalyzer(file_name)
        print(analyzer)
    
    # Otherwise, tell user and quit
    else:
        print("Error: File " + args.file_name + " does not exist")

main()
