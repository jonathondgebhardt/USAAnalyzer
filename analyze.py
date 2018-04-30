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
#       transaction is gas bought at the same gas station. Red bulls
#       and gas should be differntiated. Right now, they're lumped
#       into the same category, and as a result, the analysis is imprecise.
#
#       Conform to PEP8
#
#       Use transaction class
#


import re
import os.path
import argparse


class Transaction:

    # TODO: Fix Transaction instantiations
    def __init__(self, name, transaction_type, transaction_list):
        self.name = name
        #1: "deposit", 2: "misc", 3: "grocery", 4: "restaurant", 5: "bill", 6: "coffee", 7: "saving"
        self.transaction_type = transaction_type
        self.transaction_dates = []
        self.transaction_total = 0
        self.transaction_list.append(transaction_list)

    def __str__(self):
        return self.name + ": " + self.transaction_type + ", " + str(self.transaction_list)

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        
        # if self.name != other.name:
        #     return False
        
        # self_date = self.transaction_list[0][0]
        # self_money = self.transaction_list[0][1]
        # #print('checking', self_date, 'against', str(other.transaction_list))
        # for t in other.transaction_list:
        #     if self_date == t[0] and self_money == t[1]:
        #         return True

        # return False

        return self.name == other.name and self.transaction_type == other.transaction_type

        
    def get_transaction_total(self):
        total = 0
        
        for t in self.transaction_list:
            total += t[1]
        
        return total


class USAAnalyzer:

    _money_pattern = re.compile('\d*[,]*\d+\.\d+')
    _classifiers = {1: "deposit", 2: "misc", 3: "grocery", 4: "restaurant", 5: "bill", 6: "coffee", 7: "saving"}
    _portions = []
    _collectors = []
    _transactions = []

    def __init__(self, file_name):
        # Open file for reading
        with open(file_name, "r") as f:
            line = f.readline()
           
            # Skip information I don't know how to handle yet
            while line:
                if line == "    DEPOSITS AND OTHER CREDITS\n":
                    break
                line = f.readline()
            
            # Build a list of transactions. It will contain debits and deposits
            # together.
            self._get_transactions(f)

        # Condense the list to make it more succinct
        self._condense_transactions()

        # Retrieve a list of collectors. Add unknown ones if necessary. 
        if os.path.isfile(".collectors"): 
            # If collectors file doesn't exist, read from file
            print("Found collectors file")
            self._read_collector_file()
            
        else:
            # No list of collectors in working directory, build one from
            # list of deposits and debits and write contents to file
            print("Collectors file not found, performing setup")
            self._write_collector_file()

        # TODO: classify transactions

        
    def __str__(self):
        portions, deposit_total, debit_total = self._get_portions()
        val_total = 0.0
        result = ""
        open_string = "{}:\n{:10.2f} -- {:.2%}"

        result = ""
        for t in self._transactions:
            result += str(t) + '\n'

        # for line in portions:
        #     val = 0.0

        #     if line[0] == "deposit":
        #         val = line[1] / deposit_total
        #     else:
        #         val = line[1] / debit_total
        #         val_total += val

        #     result += "\n" + open_string.format(line[0], line[1], val)

        return result

    #
    # Creates a useful handle for where money goes to or comes from, called
    # a collector. I'm assuming these collectors are unique so that I can 
    # classify them as to what kind of transaction it is: bill, gas, etc.
    #
    def _get_collector_string(self, line):
        result = ""
        for token in line:
            if len(token) > 0:
                result += token + " "

        return result.strip()

    #
    # Parses an input file until a specified stop point. Uses a regular
    # expression to match a money line. Handles the special case for 
    # USAA internal transactions and generic transactions given the
    # file comes from USAA.
    #
    def _get_transactions(self, f):
        transaction_type = 'deposit'
        
        line = f.readline()
        while line:
            
            # Break at next section
            if line == ' ACCOUNT BALANCE SUMMARY\n':
                break
            elif line == '    OTHER DEBITS\n':
                transaction_type = 'debit'
            
            tokens = line.split(" ")

            # Parse tokens looking for money pattern
            for token in tokens:
                if self._money_pattern.match(token):
                    date = tokens[0]                      # date is first index
                    money = float(token.replace(",", "")) # remove commas
                    
                    # USAA formats their statements so that internal transactions
                    # only have one line. Consequently, if it's not an internal 
                    # transaction, read next line to get collector. Otherwise, trim
                    # up line appropriately.
                    if "USAA" not in tokens:
                        line = f.readline()
                        tokens = line.split(" ")

                    else:
                        tokens = tokens[10:]

                    name = self._get_collector_string(tokens)

                    transaction = Transaction(name, transaction_type, [date, money])
                    self._transactions.append(transaction)

            line = f.readline()
          
    #
    # Group transactions by transaction name in order to make list
    # more concise.
    #
    def _condense_transactions(self):
        new_transaction_list = []
        
        for i in range(len(self._transactions)):
            current = self._transactions[i]

            # If the transaction is not already in the list, add it to the list
            if current not in new_transaction_list:
                new_transaction_list.append(current)
            
            # Otherwise, we need to find the matching name and add dates/money
            else:
                for t in new_transaction_list:
                    if t.name == current.name:
                        t.transaction_list.append(t.transaction_list.pop())
            
            #print('length of list:', len(new_transaction_list))
                
        for t in new_transaction_list:
            if t.name == 'WSU PR ACCOUNT PAYROLL ***********4257':
                for n in t.transaction_list:
                    print(len(n))

        self._transactions = new_transaction_list

    #
    # Helper function for _condense_transactions. Overriding the __eq__
    # function will eliminate the need of this function.
    #
    def _contains(self, arr, item):
        for a in arr:
            if a.name == item.name:
                return True

        return False

    #
    # Builds a list of money spent on classifcation type. Returns 
    # the list, deposit total, debit total.
    #
    def _get_portions(self):
        temp = []
        debit_total, deposit_total = 0.0, 0.0

        # Prefill temp with known class types and initial money value. 
        # Class types are retrieved from the value position in the dictionary.
        for k, v in self._classifiers.items():
            new_line = [v, 0.0]
            if new_line not in temp:
                temp.append(new_line)


        # Iterate list incremementing appropriate class total
        # for transaction in self._deposits:
        #     temp[0][1] += transaction[2] 
        #     deposit_total += transaction[2]

        # for transaction in self._debits:
        #     for record in temp:
        #         if record[0] == self._classifiers.get(transaction[0]):
        #             record[1] += transaction[2] # increment money
        #             debit_total += transaction[2]

        for t in self._transactions:
            if t.transaction_type == 'deposit':
                # The first index in temp is deposit so we can reference
                # it directly. Increment the deposit's total by that amount
                # and increment our counter by that amount.
                temp[0][1] += t.get_transaction_total()
                deposit_total += t.get_transaction_total()
            else:
                # TODO: Need to increment by appropriate class
                continue

        return temp, deposit_total, debit_total 

    #
    # TODO: Implement this function
    #
    # Builds a file of collectors and class types. This file is stored
    # in the working directory and should be appended to when new 
    # collectors are found.
    #
    def _write_collector_file(self):
        #with open(".collectors", "w") as f:
            
            # Skip collector input on deposits since they're all same class
            # print("--- Beginning deposits ---")
            # for t in self._deposits:
            #     self._collectors.append([line[0], "deposit"])
            #     f.write(line[0].strip() + ", deposit\n")

            # print("--- Beginning debits ---")
            # for line in self._debits:
            #     collector_type = self._get_collector_input(line)
            #     self._collectors.append([line[0], collector_type])
            #     f.write(line[0].strip() + ", " + collector_type + "\n")

        return 'TODO: Implement _write_collector_file'

    #
    # Helper function for build collectors. Prompts user for what kind of 
    # classification should be applied to a collector and returns approved
    # classification type. I would ultimately like to expand the user 
    # interaction with this function: if the user doesn't recognize what
    # the transaction is, print the most recent transaction with money spent
    # and date. I want to avoid using the OOP with this project so I will
    # side with a simpler approach.
    #
    def _get_collector_input(self, collector):
        answer = "???"

        # Emulate apt-get package manager style validation. Yes is 
        # default so allows user to type Y, y or press enter. Any
        # other input is treated as a "no". Iterate until user is
        # satisfied with class type for collector.
        while answer != "" and answer != "y" and answer != "Y":

            k = None
            print("\n1. Deposit\n2. Miscellaneous\n3. Grocery\n4. Restaraunt\n5. Bill\n6. Coffee\n7. Savings\n0. Other\nPlease enter collector code for " + collector[0] + ": ", end = "")

            while k is None:
                try:
                    k = int(input())

                    if (k < 0 or k > 7):
                        print("Invalid input, try again: ", end = "")

                except ValueError or TypeError:
                    print("Invalid input, try again: ", end = "")
                    k = None


            if k == 0:
                collector_type = input("Please enter new type: ")
            else:
                collector_type = self._classifiers.get(k)
        
            answer = input("Set " + collector[0] + " as " + collector_type + " [Y]\\n?: ")


        return collector_type

    #
    # TODO: Handle transaction objects instead of strings
    #
    # Builds a list of collectors from a file. Parses current list of deposits and
    # debits to add new collectors if necessary.
    #
    def _read_collector_file(self):
        # Build list of collectors from file
        with open(".collectors", "r") as f:
            line = f.readline()

            while line:
                temp = line.split(", ")
                temp[1] = temp[1].strip()
                self._collectors.append(temp)
                line = f.readline()

        # Append to an existing file containing collectors
        with open(".collectors", "a") as f:
            # for transaction in self._deposits:
            #     # If the collector isn't found in the list of collectors,
            #     # prompt user for collector type and append to file. I can
            #     # skip collector input for deposits since they are all the
            #     # same class.
            #     if not self._has_collector(transaction[0]):
            #         print("--- Adding new deposits ---")
            #         self._collectors.append([transaction[0], "deposit"])
            #         f.write(transaction[0].strip() + ", deposit\n")

            # for transaction in self._debits:
            #     if not self._has_collector(transaction[0]):
            #         print("--- Found new debit ---")
            #         collector_type = self._get_collector_input(transaction)
            #         self._collectors.append([transaction[0], collector_type])
            #         f.write(transaction[0].strip() + ", " + collector_type + "\n")
            for t in self._transactions:
                # If the collector isn't found in the list of collectors,
                # prompt user for collector type and append to file.
                if not self._has_collector(t.name):
                    print("--- Adding new transactions ---")
                    self._collectors.append([t.name, t.transaction_type])
                    f.write(t.name, ',', t.transaction_type, '\n')      

    #
    # Helper function for get collector. Emulates Java .contains function for
    # a list of collectors.
    #
    def _has_collector(self, collector):
        for line in self._collectors:
            if line[0] == collector:
                return True

        return False 


def main():
    # Handle args 
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="name of raw USAA bank statement to be analyzed")
    args = parser.parse_args()
    
    #WSU PR ACCOUNT PAYROLL ***********4257: deposit, [['02/01', 150.23]]
    # t1 = Transaction('WSU PR ACCOUNT PAYROLL ***********4257', 'deposit', ['02/01', 150.23])
    # t2 = Transaction('WSU PR ACCOUNT PAYROLL ***********4257', 'deposit', ['02/15', 187.72])

    # print(t1 == t2)

    # l1 = [t1]

    # print(t2 not in l1)

    # If arg file is valid, continue
    if os.path.isfile(args.file_name) is not None:
        analyzer = USAAnalyzer(args.file_name)
        print(analyzer)
        
    else:
        print("Error: File " + args.file_name + " does not exist")


main()