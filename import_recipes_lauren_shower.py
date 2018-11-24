#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#

from __future__ import print_function

# From https://github.com/AKuederle/Py-Tex-automation-example/blob/POC/parser.py
import re #Regular expression
import os
import shutil
# End

__author__ = 'lfsturdy@gmail.com (Lauren Sturdy)'

import sys

from oauth2client import client
from googleapiclient import sample_tools
from collections import OrderedDict #Enables ordered dictionary
from titlecase import titlecase #Enables smart title capitalization function

def main(argv):
    # Authentication modified from https://github.com/google/google-api-python-client/blob/master/samples/blogger/blogger.py
    # Authenticate and construct service.
    try:
        service, flags = sample_tools.init(
           argv, 'sheets', 'v4', __doc__, __file__,
           scope='https://www.googleapis.com/auth/spreadsheets.readonly')
    except: 
        print ('You are not connected to the internet. Fix that and try again')
        return
    
    #Read in from the spreadsheet. From https://developers.google.com/sheets/quickstart/python
    try:
        spreadsheetId = '1-_qfPObOO6UyozFPA4X9dJEyfDS3BlKFj9WuAjxqEVM' #Id of the spreadsheet with responses
        rangeName = 'PyCat!A2:K'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId, range=rangeName).execute()             
    except client.AccessTokenRefreshError:
        print ('The credentials have been revoked or expired, please re-run'
            'the application to re-authorize')
            
    # Get categories in use from the table
    cats = result.get('values', []) 
    categories = OrderedDict() #Using ordered dictionary to facilitate making cookbook later
    for entry in cats:
        categories[entry[0]] = entry[1:]
    #print(categories)
    
    #Now get all of the actual recipes
    rangeName = 'Responses!A2:L' #Make sure that the last column is required
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()                
      
    values = result.get('values', [])
    
    recipelist = {} #Initialize dictionary for recipes by category
    project = "LIfiles"
    if not values: #Nothing was retrieved from the spreadsheet
        print('No data found.')
    else:
        for row in values: #Process each recipe (which is its own spreadsheet row)
            #This code parses the row and prints the data to a .tex file        
            title = titlecase(fixstring(row[1])) #Fixes case as well
            source = fixstring(row[2])
            notes = fixstring(row[3]).replace(u'\n', u" ") #Remove line breaks in notes
            servings = fixstring(row[4])
            category = fixstring(row[5])
            ingred = fixstring(row[9])
            direct = fixstring(row[10])
            carbs = ""
            subcat = []
            for cat in row[6:9]: #Since subcategories are in three columns
                if cat: subcat = fixstring(cat)
                 
            filename = title.replace(" ", "") #Filename is the title minus spaces
            filename = filename.replace("\"", "") #Filename also remove quotes
            filename = filename.replace("/", "") 
            recipefile = open(project+"\\"+filename+".tex", "w")

            ingred = stding(ingred) #Standardize ingredients
            direct = stddir(direct) #Standardize directions (fewer changes than ingredients)

            recipefile.write("\\begin{recipe}{"+title+"}{"+source+"}{"+servings+
                "}{"+carbs+"}{"+notes+"}\n\\begin{ing}{2}"+ingred+
                "\n\end{ing}\n\index{Bread}\n\\label{"+filename.lower()+"}\n"+direct+"\n\end{recipe}")
                
            recipefile.close()
            
            #The recipe needs to be filed by category for printing (category, subcat)
            
            if subcat: #If there are subcategories
                recipelist.setdefault(category+":"+subcat,[]).append(filename)
            else: recipelist.setdefault(category,[]).append(filename)
        
        #Write the main content file which will call the recipes   
        cookbookfile = open(project+"\\recipes.tex", "w")
        print(recipelist)
        for maincat in categories: 
            if [(k, v) for (k, v) in recipelist.iteritems() if maincat in k]: #If there is a recipe with that main header
                cookbookfile.write("\\addchap{"+maincat+"}\n")
                if categories[maincat]: #If there are subcategories
                    for subcat in categories[maincat]:
                        if maincat + ":" + subcat in recipelist:
                            cookbookfile.write("\t\\addsec{"+subcat+"}\n")
                            for list in recipelist[maincat + ":" + subcat]:
                                cookbookfile.write("\t\t\\input{" + list + "}\n")
                        
                else:
                    #print(recipelist)
                    for list in recipelist[maincat]:
                        cookbookfile.write("\t\\input{" + list + "}\n")
        cookbookfile.close()
        
        #Modified from https://github.com/AKuederle/Py-Tex-automation-example/blob/POC/parser.py
        
        build_d = "{}".format(project)
        out_file = "{}/LaurenCookbook".format(build_d)
        os.system("pdflatex -output-directory {} {}".format(os.path.realpath(build_d), os.path.realpath(out_file)))
        os.system("makeidx -output-directory {} {}".format(os.path.realpath(build_d), os.path.realpath(out_file)))
        os.system("pdflatex -output-directory {} {}".format(os.path.realpath(build_d), os.path.realpath(out_file)))
        #This copies the pdf into the root folder for the .py code
        shutil.copy2(out_file+".pdf", os.path.dirname(os.path.realpath(project)))
        #End
            
def fixstring(string):
    # Replaces non-ascii symbols and LaTeX incompatible symbols with appropriate replacements
    try:
        string = string.replace(u'\u2019', u"'") #Replace left single quote
        string = string.replace(u'\xd7', u'x') #Replace multiplication x
        string = string.replace(u'\xb0 ', u'\degrees ') #Replace degree symbol with space after with defined function
        string = string.replace(u'\xb0', u'\degree ') #Replace degree symbol without space with defined function
        string = string.replace(u'\xba', u'\degree ') # MASCULINE ORDINAL INDICATOR
        string = string.replace(u'\xba ', u'\degrees ') # MASCULINE ORDINAL INDICATOR
        string = string.replace(u'\u201c', u"``") #Replace left double quotes
        string = string.replace(u'\u201d', u"''") #Replace right double quotes
        string = string.replace(u'\xe9', u"\\'e") #Accented e
        string = string.replace(u'\xbd', u"\half") #vulgar half
        string = string.replace(u'\xbc', u"\quart") #vulgar quarter
        string = string.replace(u'\xbe', u"\tquart") #vulgar three quarters
        string = string.replace(u'\u2153', u'\\third') #vulgar third (and t)
        string = string.replace(u'\u2154', u'\\tthird') #vulgar two-thirds
        string = string.replace(u'\u2014', u'---') #em-dash
        string = string.replace(u'_', u'\_') #underscores are protected in LaTeX
        string = string.replace(u'\u223C', u'$\sim$') #LaTeX doesn't deal with tildes
        string = string.replace(u'\u007E', u'$\sim$') #LaTeX doesn't deal with tildes
        string = string.rstrip() #Remove whitespace at the end--this can cause problems in LaTeX
        string = string.replace(u'&', u' and ')
        #I need to indicate links by putting a \url wrapper on it. The code for the regex is based
        #on one I found here: https://code.tutsplus.com/tutorials/8-regular-expressions-you-should-know--net-6149
        string = re.sub(r'((https?:\/\/)?(www\.)([\da-z-]+)\.([a-z\.]{2,6})([\/\w\\\.-]*))', r'\url{\1}', string)
        string = re.sub(r'(\d\d\d)\s?\\?(degree)?s?((\s?[C|F])|)?', r'\1\\degrees \3', string) #Add space between degree symbol and C or F
        string = re.sub(r'(\d\d\d)(?!\\)', r'\1\\degree ', string) #Add a degree symbol to any number not followed by a space or slash
        string = re.sub(r'(\\degrees)(?=( *\.))', r'\\degree ', string) #Correct any extra spaces added before periods

    except IOError, (ErrorNumber, ErrorMessage):
        print(ErrorMessage)
    return string

def stding(string): #Function to analyze the ingredients and output a properly formatted string
    # The following replacements all standardize the notation and add 
    # LaTeX markup for certain symbols.

    string = string.replace(u'cups', u'C')
    string = string.replace(u'Cups', u'C')
    string = string.replace(u'Cup', u'C')
    string = string.replace(u'cup', u'C')
    string = string.replace(u' c ', u' C ')
    string = string.replace(u'tablespoons', u'Tbsp')
    string = string.replace(u'tablespoon', u'Tbsp')
    string = string.replace(u' T ', u' Tbsp ')
    string = string.replace(u'Tbs ', u'Tbsp')
    string = string.replace(u'teaspoons', u'tsp')
    string = string.replace(u'teaspoon', u'tsp')
    string = string.replace(u' t ', u' tsp ')
    string = string.replace(u'grams', u'g')
    string = string.replace(u'gram', u'g')
    string = string.replace(u'ounces', u'oz')
    string = string.replace(u'ounce', u'oz')
    # Spaces are added to make sure there is a space between numbers and 
    # words. Double spaces won't show up.
    string = string.replace(u'1/4', u'\quart ')
    string = string.replace(u'1/2', u'\half ')
    string = string.replace(u'3/4', u'\\tquart ')
    string = string.replace(u'1/3', u'\\third ') #The extra slash means it isn't a tab
    string = string.replace(u'2/3', u'\\tthird ')
    string = string.replace(u'1/8', u'\eighth ')
    string = string.replace(u'optional', u'opt.')
    
    # The following fixes the spacing between elements
    string = re.sub(r'(\d) (\\)', r'\1\2', string) # Look for numbers followed by spaces by a slash and deletes the space
    string = string.replace(u'\n', u'\n\n') #LaTeX newlines require two (could also be "\\", but newlines are easier to read in the file)
    
    numlines = string.count("\n") #Count the number of new lines
    if numlines < 3: #Assume that a recipe will have at least three ingredients
        #If there are not three ingredients, assume that they didn't read 
        #the directions and are using a different separator.
        string = string.replace(u', ', u'\n\n') #Since it's adding a new line, remove the space after the comma
        
    return string    
    
def stddir(string): #Function to analyze the directions and output a properly formatted string
    # The following replacements all standardize the notation and add 
    # LaTeX markup for certain symbols.

    # Spaces are added to make sure there is a space between numbers and 
    # words. Double spaces won't show up.
    string = string.replace(u'1/4', u'\quart ')
    string = string.replace(u'1/2', u'\half ')
    string = string.replace(u'3/4', u'\\tquart ')
    string = string.replace(u'1/3', u'\\third ') #The extra slash means it isn't a tab
    string = string.replace(u'2/3', u'\\tthird ')
    string = string.replace(u'1/8', u'\eighth ')
    string = string.replace(u'optional', u'opt.')
    

    # Replace "degrees" with the degree symbol
    #string = re.sub(r'(?<!\\)\s?degrees?\s(C|F)',r'\\degrees \1', string) #find instances of "degrees F", "degree C", etc. and replace with symbol and C or F
    #string = re.sub(r'(?<!\\)\s?degrees?\s', r'\\degrees ', string) #If space after, use degrees
    #string = re.sub(r'(?<!\\)\s?degrees?', r'\\degree ', string)
    #string = re.sub(r'(\d\d\d) (\\?degrees?)? ?(C|F)', r'\1\\degrees \3', string)
    #string = re.sub(r'(\d\d\d) (\\?degrees?)?', r'\1\\degrees ', string)
    #string = re.sub(r'(\d\d\d)(?!(\s|\\))(C|F)', r'\1\\degrees \3', string)
        
    # The following fixes the spacing between elements
    string = re.sub(r'(\d) (\\)', r'\1\2', string) # Look for numbers followed by spaces by a slash and deletes the space
    string = string.replace(u'\n', u'\n\n') #LaTeX newlines require two (could also be "\\", but newlines are easier to read in the file)
    #Add regular expression for pan size -- 9"x13"
        
    return string    

if __name__ == '__main__':
  main(sys.argv)
