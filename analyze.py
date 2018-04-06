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

    def __init__(self, name, transaction_type, transaction_list):
        self.name = name
        self.transaction_type = transaction_type
        self.transaction_list = transaction_list

    def __str__(self):
        return self.name + ": " + self.transaction_type + ", " + str(self.transaction_list)
        
    def set_transaction_type(self, transaction_type):
        # 1: "deposit", 2: "misc", 3: "grocery", 4: "restaurant", 5: "bill", 6: "coffee", 7: "saving"
        self.transaction_type = transaction_type
    
    def add_transaction(self, new_transaction):
        # Expecting a tuple: (date, amount)
        self.transaction_list.append(new_transaction)

    def get_transaction_total(self):
        total = 0
        
        for t in self.transaction_list:
            total += t[1]
        
        return total

    


class USAAnalyzer:

    _money_pattern = re.compile('\d*[,]*\d+\.\d+')
    _collector_types = {1: "deposit", 2: "misc", 3: "grocery", 4: "restaurant", 5: "bill", 6: "coffee", 7: "saving"}
    #_deposits = []
    #_debits = []
    _portions = []
    _collectors = []
    _classifiers = {}
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
            
            # Build a list of deposits and debits.These lists are 
            # condensed, meaning that each collector takes at most one line
            # self._deposits = self._get_transactions(f, "    OTHER DEBITS\n")
            # self._debits = self._get_transactions(f, " ACCOUNT BALANCE SUMMARY\n")
       
            self._get_transactions(f)

        self._condense_transactions()

        # Retrieve a list of collectors. Add unknown ones if necessary. 
        if os.path.isfile(".collectors"): 
            # If collectors file doesn't exist, read from file
            print("Found collectors file")
            collectors = self._get_collectors()
            
        else:
            # No list of collectors in working directory, build one from
            # list of deposits and debits and write contents to file
            print("Collectors file not found, performing setup")
            self._build_collectors()

        # should condense transactions here

        # Build a dictionary s.t. keys are classification types and values
        # are total amount spent on that type
        self._get_classifiers(collectors)

        
    
    def __str__(self):
        portions, deposit_total, debit_total = self._get_portions()
        val_total = 0.0
        result = ""
        open_string = "{}:\n{:10.2f} -- {:.2%}"

        for line in portions:
            val = 0.0

            if line[0] == "deposit":
                val = line[1] / deposit_total
            else:
                val = line[1] / debit_total
                val_total += val

            result += "\n" + open_string.format(line[0], line[1], val)

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
    # Helper function for making transaction list more concise. Returns
    # index of collector if it's in the list, -1 otherwise.
    #
    def _get_index(self, arr, collector):
        index = 0
        for line in arr:
            if line[0] == collector:
                return index
            index += 1

        return -1


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
                    #new_line = [name, date, money]

                    transaction = Transaction(name, transaction_type, [date, money])
                    self._transactions.append(transaction)
                    #temp.append(new_line)

            line = f.readline()
        
        
    def _condense_transactions(self):
        # TODO: Is this necessary? It might be creating problems.
        #
        # Now that we've built a list of transactions, make the list more 
        # concise by combining common collectors. Do this by appending dates
        # and incrementing total money spent or deposited.
        # transactions = []
        # for transaction in temp:
        #     index = self._get_index(transactions, transaction[0])

        #     if index != -1:
        #         transactions[index][1] += ", " + transaction[1] # append dates
        #         transactions[index][2] += transaction[2]        # increment total
        #     else:
        #         transactions.append(transaction)

        temp_transaction_list = []
        
        for i in range(len(self._transactions)):
            t = self._transactions[i]
            collector = t.name
            collector_total = 0

            for j in range(i, len(self._transactions)):
                if (self._transactions[j].name == collector):
                    collector_total += self._transactions[j].get_transaction_total()
                
                print(collector, collector_total)



        return 0

    #
    # Builds dictionary of known classification types from argument file. Arrangement
    # is "Collector Handle": "Classification". Returns the dictionary.
    #
    def _get_classifiers(self, collectors):
        for line in self._collectors:
            # first index is collector, second is class
            self._classifiers[line[0]] = line[1].strip()


    #
    # TODO: Handle transaction objects instead of strings
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
                temp[0][1] += t.getTransactionTotal
                deposit_total += transaction[2]

        return temp, deposit_total, debit_total 


    #
    # TODO: Handle transaction objects instead of strings
    # TODO: Also show user when they made transaction and for how much?
    #
    # Builds a file of collectors and class types. This file is stored
    # in the working directory and should be appended to when new 
    # collectors are found.
    #
    def _build_collectors(self):
        with open(".collectors", "w") as f:
            
            # Skip collector input on deposits since they're all same class
            print("--- Beginning deposits ---")
            for line in self._deposits:
                self._collectors.append([line[0], "deposit"])
                f.write(line[0].strip() + ", deposit\n")

            print("--- Beginning debits ---")
            for line in self._debits:
                collector_type = self._get_collector_input(line)
                self._collectors.append([line[0], collector_type])
                f.write(line[0].strip() + ", " + collector_type + "\n")


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
                collector_type = self._collector_types.get(k)
        
            answer = input("Set " + collector[0] + " as " + collector_type + " [Y]\\n?: ")


        return collector_type


    #
    # TODO: Handle transaction objects instead of strings
    #
    # Builds a list of collectors from a file. Parses current list of deposits and
    # debits to add new collectors if necessary.
    #
    def _get_collectors(self):
        # Build list of collectors from file
        with open(".collectors", "r") as f:
            line = f.readline()

            while line:
                temp = line.split(", ")
                self._collectors.append(temp)

                line = f.readline()

        # Append to an existing file containing collectors
        with open(".collectors", "a") as f:
            for transaction in self._deposits:
                # If the collector isn't found in the list of collectors,
                # prompt user for collector type and append to file. I can
                # skip collector input for deposits since they are all the
                # same class.
                if not self._has_collector(transaction[0]):
                    print("--- Adding new deposits ---")
                    self._collectors.append([transaction[0], "deposit"])
                    f.write(transaction[0].strip() + ", deposit\n")

            for transaction in self._debits:
                if not self._has_collector(transaction[0]):
                    print("--- Found new debit ---")
                    collector_type = self._get_collector_input(transaction)
                    self._collectors.append([transaction[0], collector_type])
                    f.write(transaction[0].strip() + ", " + collector_type + "\n")


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
    
    # If arg file is valid, continue
    if os.path.isfile(args.file_name) is not None:
        analyzer = USAAnalyzer(args.file_name)
        print(analyzer)
        
    else:
        print("Error: File " + args.file_name + " does not exist")


main()

