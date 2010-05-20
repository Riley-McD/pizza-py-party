#!/usr/bin/env python

import os
import sys
import getopt
import re
import urllib2
import cookielib
from xml.dom import minidom as dom
import htmllib
import formatter
from urllib import urlencode
from getpass import getpass

# Some function aliases and set up cookie management
urlopen = urllib2.urlopen
Request = urllib2.Request
cj = cookielib.LWPCookieJar ()
opener = urllib2.build_opener (urllib2.HTTPCookieProcessor (cj))
urllib2.install_opener (opener)

# Page Urls. Urls are typically references to previous pages visited.
# There are lots of them.
# Change in pages are dependent on the post data passed
# (via the goTo or _idcl variable depending on the page and method)
# TODO (ryochan7): Get rid of all non-essential urls. Grab urls from the action
#                  attribute in forms
LOGIN_URL = "https://www01.order.dominos.com/olo/faces/login/login.jsp"
CHOOSE_PIZZA_URL = "https://www01.order.dominos.com/olo/faces/order/step1_start_order.jsp"
COUPON_PAGE_URL = CHOOSE_PIZZA_URL
ADD_COUPON_URL = "https://www01.order.dominos.com/olo/faces/order/coupons.jsp"
BUILD_PIZZA_URL = "https://www01.order.dominos.com/olo/faces/order/step2_choose_pizza.jsp"
ADD_PIZZA_URL = "https://www01.order.dominos.com/olo/faces/order/step2_build_pizza.jsp"
CALCULATE_TOTAL_URL = "https://www01.order.dominos.com/olo/servlet/ajax_servlet"
CALCULATE_TOTAL_URL_POST_VARS = {
    "cmd": "priceOrder",
    "formName": "orderSummaryForm:",
    "getFreeDeliveryOffer": "N",
    "runCouponPicker": "N",
    "runPriceOrder": "Y",
}
ADD_SIDES_URL = ADD_PIZZA_URL
CHECKOUT_URL = "https://www01.order.dominos.com/olo/faces/order/step3_choose_drinks.jsp"
SUBMIT_ORDER_URL = "https://www01.order.dominos.com/olo/faces/order/placeOrder.jsp"
LOGOUT_URL = "http://www01.order.dominos.com/olo/servlet/init_servlet?target=logout"

# Set User Agent
VERSION_NUM = "0.2.2"
USER_AGENT = {'User-agent' : 'PizzaPyParty/%s' % VERSION_NUM}

# TODO (ryochan7): Organize toppings data strutures in a better manner
# Lists with default pizza attributes. Used when parsing pizza options passed
sizes = ("small", "medium", "large", "x-large")
crusts = ("handtoss", "deepdish", "thin", "brooklyn")
#TOPPING_CHEESE, TOPPPING_SAUSE = ("toppingC", "toppingX")
TOPPING_CHEESE, TOPPPING_SAUSE = ("topping-#-C-#-", "topping-#-X-#-")
toppings = ['p', 'x', 'i', 'b', 'h', 'c', 'k', 's',
    'g', 'l', 'a', 'm', 'o', 'j', 'e', 'd', 'n', 'v', 't']

###################################
####                           ####
####     Topping info          ####
####                           ####
###################################

#topping(code): code will specify if a topping is selected
#toppingSide(code): W - Whole Pizza
#                   1 - Left Side Only
#                   2 - Right Side Only
#                   Will only allow on whole pizza for the time being
#toppingAmount(code):  1 - Normal
#                     .5 - Light
#                    1.5 - Extra
#                    Will only allow normal amount of topping


#### CHEESE & SAUCE ####
#toppingCHEESE:  Cheese (Irrelevant. Use toppingC)
#toppingC: toppingSideC: toppingAmountC: Cheese
#### Side seems irrelevant when it comes to sauce
#toppingSAUCE: toppingAmountSAUCE: Sauce (Irrelevant. Use specific sauce topping)
#toppingX: toppingSideX: toppingAmountX: New Robust Tomato Sauce
#toppingXw: toppingSideXw: toppingAmountXw: White Sauce
#toppingXm: toppingSideXm: toppingAmountXm: Hearty Marinara Sauce
#toppingBq: toppingSideBq: toppingAmountBq: BBQ Sauce

#### MEATS ####
#toppingP: toppingSideP: toppingAmountP: Pepperoni: 
#toppingPl: toppingSidePl: toppingAmountPl: Extra Large Pepperoni
#toppingSb: toppingSideSb: toppingAmountSb: Sliced Italian Sausage
#toppingS: toppingSideS: toppingAmountS: Italian Sausage
#toppingB: toppingSideB: toppingAmountB: Beef
#toppingH: toppingSideH: toppingAmountH: Ham
#toppingK: toppingSideK: toppingAmountK: Bacon
#toppingDu: toppingSideDu: toppingAmountDu: Premium Chicken
#toppingSa: toppingSideSa: toppingAmountSa: Salami
#toppingPm: toppingSidePm: toppingAmountPm: Philly Steak

#### UNMEATS ####
#toppingG: toppingSideG: toppingAmountG: Green Peppers
#toppingR: toppingSideR: toppingAmountR: Black Olives
#toppingN: toppingSideN: toppingAmountN: Pineapple
#toppingM: toppingSideM: toppingAmountM: Mushrooms
#toppingO: toppingSideO: toppingAmountO: Onions
#toppingJ: toppingSideJ: toppingAmountJ: Jalapeno Peppers
#toppingZ: toppingSideZ: toppingAmountZ: Banana Peppers
#toppingSi: toppingSideSi: toppingAmountSi: Spinach
#toppingRr: toppingSideRr: toppingAmountRr: Roasted Red Peppers
#toppingE: toppingSideE: toppingAmountE: Cheddar Cheese
#toppingCp: toppingSideCp: toppingAmountCp: Shredded Provolone Cheese
#toppingCs: toppingSideCs: toppingAmountCs: Shredded Parmesan
#toppingFe: toppingSideFe: toppingAmountFe: Feta Cheese
#toppingV: toppingSideV: toppingAmountV: Green Olives
#toppingTd: toppingSideTd: toppingAmountTd: Diced Tomatoes
#toppingHt: toppingSideHt: toppingAmountHt: Hot Sauce


toppings_long = [
    "pepperoni",
    "xlarge-pepperoni",
    "italian-sausage",
    "beef",
    "ham",
    "bacon",
    "chicken",
    "philly-steak",
    "green-peppers",
    "black-olives",
    "pineapple",
    "mushrooms",
    "onions",
    "jalapeno-peppers",
    "banana-peppers",
    "cheedar-cheese",
    "provolone-cheese",
    "green-olives",
    "tomatoes",
]

toppings_cryptic = {
    "pepperoni":        "P",
    "xlarge-pepperoni": "Pl",
    "italian-sausage":  "S",
    "beef":             "B",
    "ham":              "H",
    "bacon":            "K",
    "chicken":          "Du",
    "philly-steak":     "Pm",
    "green-peppers":    "G",
    "black-olives":     "R",
    "pineapple":        "N",
    "mushrooms":        "M",
    "onions":           "O",
    "jalapeno-peppers": "J",
    "banana-peppers":   "Z",
    "cheedar-cheese":   "E",
    "provolone-cheese": "Cp",
    "green-olives":     "V",
    "tomatoes":         "Td",
}

help_text = (
    "            With Pepperoni",   "     With Extra Large Pepperoni",
    "      With Italian Sausage",   "                 With Beef",
    "                  With Ham",   "                With Bacon",
    "              With Chicken",   "         With Philly Steak",

    "        With Green Peppers",   "         With Black Olives",
    "            With Pineapple",   "            With Mushrooms", 
    "               With Onions",   "     With Jalapeno Peppers",
    "       With Bananan Peppers",
    "       With Cheedar Cheese",     "     With Provolone Cheese",
    "         With Green Olives", "             With Diced Tomatoes",)
toppings_dict = {}
for i, topping in enumerate (toppings_long):
    toppings_dict.update ({topping: {
        'short': toppings[i],
        'long': topping, 'help_text': help_text[i],
        'cryptic_name': "topping%s" % toppings_cryptic[topping],
        'cryptic_num': "toppingSide%s" % toppings_cryptic[topping]}}
    )
del toppings_cryptic
del help_text

# Dictionary used for pizza
default_pizza = {}.fromkeys (toppings_long, ['', '1'])
default_pizza.update ({'crust': 'HANDTOSS'})
default_pizza.update ({'size': '10'})
default_pizza.update ({'quantity': '1'})
default_pizza.update ({'cheese': ['W', '1']})
default_pizza.update ({'sauce': ['W', '1']})


# Set the minimum and maximum amount of pizzas that can be ordered
MIN_QTY = 1
MAX_QTY = 25
MAX_TOTAL_QTY = 25
ORDERED_PIZZAS = 0


###########################################################
#                                                         #
#       Main Pizza Class and Page Parsing Classes         #
#                                                         #
###########################################################


#TODO: ABSTRACT AND SPLIT CLASS, FIX RIGID LOGIC
class Pizza:
	def __init__ (self):
		self.crust = ""
		self.size = ""
		self.quantity = ""
		self.toppings = []
		self.order = default_pizza.copy ()


	###########################################################
	#                                                         #
	#           Pizza Attributes Parsing Functions            #
	#                                                         #
	###########################################################

	def setTopping (self, topping):
		""" Add a topping to a pizza """
		if len (topping) == 1 and topping in toppings:
			idx = toppings.index (topping)
			topping = toppings_long[idx]
		elif not topping in toppings_long:
			print >> sys.stderr, "'%s' is not a valid topping choice. Exiting." % topping
			sys.exit (42)
		self.order.update ({topping: ['W', '1']})
		if not topping in self.toppings:
			self.toppings.append (topping)


	def setQuantity (self, quantity):
		""" Sets the quantity of the pizza based on the quantity passed """
		if self.quantity:
			print >> sys.stderr, """You cannot set the quantity for the same pizza twice.
Please check your command-line parameters. Exiting."""
			sys.exit (42)
		try:
			quantity = int (quantity)
		except ValueError:
			print >> sys.stderr, "The input value for quantity must be an integer. Exiting."
			sys.exit (42)
		if quantity >= MIN_QTY and quantity <= MAX_QTY:
			global ORDERED_PIZZAS
			if (quantity + ORDERED_PIZZAS <= MAX_TOTAL_QTY):
				self.order.update ({'quantity': str (quantity)})
				self.quantity = quantity
				ORDERED_PIZZAS += quantity
			else:
				print >> sys.stderr, "You cannot order more than %i pizzas. Exiting." % MAX_TOTAL_QTY
				sys.exit (42)
		else:
			print >> sys.stderr, "Bad value for quantity. Quantity must be between %i and %i. Exiting." % (MIN_QTY, MAX_QTY)
			sys.exit (42)


	def setSize (self, size):
		""" Sets the size of the piza based on the size choice passed """
		if self.size:
			print >> sys.stderr, """You cannot set the size twice. Please check your command
line parameters. Exiting."""
			sys.exit (42)
		if size == 'small':
			# Deepdish pizzas cannot be small size.
			# Will revert to medium size
			if self.crust == 'deepdish':
				print "Small size is not available for deepdish pizzas. Changing to medium."
				self.order.update ({'size': '12'})
				self.size = 'medium'
			elif self.crust == 'brooklyn':
				print "Small size is not available for brooklyn pizzas. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			else:
				self.order.update ({'size': '10'})
				self.size = size
		elif size == 'medium':
			if self.crust == 'brooklyn':
				print "Medium size is not available for brooklyn pizzas. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			else:
				self.order.update ({'size': '12'})
				self.size = size
		elif size == 'large':
			self.order.update ({'size': '14'})
			self.size = size
		elif size == 'x-large':
			# Deepdish and thin pizzas cannot be extra large size.
			# Will revert to large size
			if self.crust == 'deepdish':
				print "Extra large size is not available for deepdish pizzas. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			elif self.crust == 'thin':
				print "Extra large size is not available for thin pizzas. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			else:
				self.order.update ({'size': '16'})
				self.size = size
		else:
			print >> sys.stderr, "'%s' is not a valid size choice. Exiting." % size
			sys.exit (42)

	def setCrust (self, crust):
		""" Sets the crust of the pizza based on the curst choice passed """
		if self.crust:
			print >> sys.stderr, """You cannot set the crust twice. Please check your
command line parameters. Exiting."""
			sys.exit (42)
		if crust == 'handtoss':
			self.order.update ({'crust': 'HANDTOSS'})
			self.crust = crust
		# Deepdish pizzas can only be of medium or large sizes
		elif crust == 'deepdish':
			if self.size == 'small':
				print "Small size is not available for deepdish pizzas. Changing to medium."
				self.order.update ({'size': '12'})
				self.size = 'medium'
			elif self.size == 'x-large':
				print "Extra large size is not available for deepdish pizzas. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			self.order.update ({'crust': 'DEEPDISH'})
			self.crust = crust
		elif crust == 'thin':
			# Thin pizzas cannot be extra large size
			if self.size == 'x-large':
				print "Extra large size is not available for thin pizzas. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			self.order.update ({'crust': 'THIN'})
			self.crust = crust
		elif crust == 'brooklyn':
			if self.size == 'small' or self.size == 'medium':
				print "The smallest available size for brooklyn pizzas is large. Changing to large."
				self.order.update ({'size': '14'})
				self.size = 'large'
			self.order.update ({'crust': 'BK'})
			self.crust = crust
		else:
			print >> sys.stderr, "'%s' is not a valid crust choice. Exiting."
			sys.exit (42)


class ParseCoupons (htmllib.HTMLParser):
    """ Parser for the coupons page. Obtains all available coupon offers """
    def __init__(self, verbose=False):
        f = formatter.NullFormatter ()
        htmllib.HTMLParser.__init__ (self, f, verbose)
        self.in_coupon_menu = False
        self.in_ul = False
        self.getcoupon = False
        self.id = ""
        self.description = ""
        self.price = -1.0 # Arbitrary non-blank default value
        self.type = ""
        self.formdata = []
        self.pattern = re.compile (r".*document\.forms\['couponsForm'\]\['couponCode'\]\.value='((?:_)?\d{4})'")


    def start_div (self, attrs):
        for item, value in attrs:
            # Get scope for full coupon listing. Helps avoid duplicates
            if item == "class" and value == "menutype seeall":
                self.in_coupon_menu = True
            elif item == "class" and value == "coupon-price" and self.in_coupon_menu:
                self.save_bgn ()
                self.type = "coupon-price"


    def end_div (self):
        # If working outside of main coupon display, ignore
        if not self.in_coupon_menu:
            return

        # Get price from text buffer
        if self.type == "coupon-price":
            text = self.save_end ()
            self.price = text.decode ("utf8", "ignore")
            self.type = ""

    def start_ul (self, attrs):
        # If working outside of main coupon display, ignore
        if not self.in_coupon_menu:
            return

        # Note beginning of coupon list
        self.in_ul = True

    def end_ul (self):
        if self.in_ul:
            # At end of coupon list
            self.in_coupon_menu = False
            self.in_ul = False


    def start_li (self, attrs):
        # If working outside of main coupon display, ignore
        if not self.in_coupon_menu or not self.in_ul:
            return

        for item, value in attrs:
            if item == "class" and value == "coupon-item" or value == "coupon-item first-item":
                self.getcoupon = True # Only set True when in "menutype seeall" div scope


    def end_li (self):
        if self.getcoupon:
            # End of coupon entry
            self.getcoupon = False


    def start_a (self, attrs):
        # If working outside of list item, ignore
        if not self.getcoupon:
            return

        for item, value in attrs:
            if item == 'onclick':
                match = self.pattern.search (value)
                if not match:
                    raise Exception ("Necessary item 'couponCode' was not found on the page")
                temp = match.group (1)
                self.id = temp
            elif item == "title":
                self.description = value


    # Append item and information to form data
    def end_a (self):
        # If working outside of list item, ignore
        if not self.getcoupon:
            return

        if self.id and self.description and self.price != -1.0:
            self.formdata.append ((self.id, self.description, self.price))
        self.id = ""
        self.description = ""
        self.price = -1.0 # Arbitrary non-blank default value
        self.type = ""


class Parser (htmllib.HTMLParser):
    """ Generic parser used to parse the pages and obtain the form data """
    def __init__(self, form_id, verbose=False):
        f = formatter.NullFormatter ()
        htmllib.HTMLParser.__init__ (self, f, verbose)
        self.form_id = form_id
        self.getform = False
        self.select_name = None
        self.option_value = None
        self.form_action = None
        self.formdata = {}


    def do_form (self, attrs):
        for item, value in attrs:
            if item == "id" and value == self.form_id:
                self.getform = True
                #return
            elif item == "action":
                self.form_action = value

        if self.getform and self.form_action:
            return

        self.getform = False


    def do_input (self, attrs):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        name = tmp_value = None
        radio_field = checked = False
        for item, value in attrs:
            if item == "name":
                name = value
            elif item == "value":
                tmp_value = value
            if item == "type" and value == "radio":
                radio_field = True
            elif item == "checked" and radio_field:
                checked = True

        if name and tmp_value != None:
            # Check if a radio field needs to be updated
            if radio_field and checked:
                self.formdata.update ({name: tmp_value})
            # Update non-radio fields
            elif not radio_field:
                self.formdata.update ({name: tmp_value})
        # Include any input with no specified value
        # (in some needed hidden fields). Ex. login:_idcl
        elif name:
            self.formdata.update ({name: ""})


    def start_select (self, attrs):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        for item, value in attrs:
            if item == "name":
                self.select_name = value


    def do_option (self, attrs):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        attrs = dict(attrs)
        value = attrs.get("value", None)
        if "selected" in attrs:
            if value is None:
                raise Exception("TODO: Support options w/o value attrs")
            self.option_value = value

        self.last_option_value = value


    def end_select (self):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        # If no option is selected (should not happend),
        # make last grabbed value the selected value
        if not self.option_value:
            self.option_value = self.last_option_value

        if self.select_name and self.option_value:
            self.formdata.update ({self.select_name: self.option_value})

        # Reset these.
        self.select_name = None
        self.option_value = None
        self.last_option_value = None


###########################################################
#                                                         #
#                   Helper Functions                      #
#                                                         #
###########################################################

def getPage (url, data=None):
    """ Generic function that makes requests for pages """
    if data != None:
        data = urlencode (data)
    try:
        req = Request (url, data, USER_AGENT)
        handle = urlopen (req)
    except:
        raise Exception ("Could not get page %s." % url)

    page = handle.read ()
    handle.close ()
    return page

def getFormData (scan_page, target_form):
    """ Calls the main Parser class to obtain the form data of a page """
    parsed_form = Parser (target_form)
    try:
        parsed_form.feed (scan_page)
    except Exception:
        dumpPage (scan_page)
    parsed_form.close ()
#    print parsed_form.formdata
    return parsed_form.formdata


def setFormField (current_data, name, new_value):
    """ Check that a particular entry exists in the form data
        and updates the entry with the value passed """
    if not name in current_data:
        raise Exception ("Necessary item \"%s\" was not found in the form.\nCurrent form data: %s" % (name, current_data))

    current_data.update ({name: new_value})

def mergeAttributes (parsed_conf, username, password, pizza):
	""" Merge attributes specified in the config file and any attributes
	    specified on the command line """
	temp_username, temp_password, temp_crust, temp_size, temp_quantity, temp_toppings = parsed_conf
	i = 0
	for current_item in parsed_conf:
		if not current_item:
			i += 1
			continue
		if i == 0:
			if not username:
				username = temp_username
		elif i == 1:
			if not password:
				password = temp_password
		elif i == 2 and current_item in crusts:
			if not pizza.crust:
				pizza.setCrust (current_item)
		elif i == 3 and current_item in sizes:
			if not pizza.size:
				pizza.setSize (current_item)
		elif i == 4 and int (current_item):
			if not pizza.quantity:
				pizza.setQuantity (current_item)
		elif i == 5:
			if not pizza.toppings:
				for new_topping in temp_toppings:
					if new_topping in toppings_long:
						pizza.setTopping (new_topping)
					else:
						print >> sys.stderr, "The topping '%s' is not valid. Exiting." % new_topping
						sys.exit (2000)						
		else:
			print >> sys.stderr, "The value '%s' is not valid. Exiting." % current_item
			sys.exit (42)
		i += 1
	return username, password

def findMissingAttributes (data_list):
	""" Find the first attribute that is blank, print what the missing
	    attribute is, and then exit """
	index = data_list.index ('')

	failed_value = ''
	if index == 0:
		failed_value = 'username'
	elif index == 1:
		failed_value = 'password'
	elif index == 2:
		failed_value = 'crust'
	elif index == 3:
		failed_value = 'size'
	elif index == 4:
		failed_value = 'quantity'
	print >> sys.stderr, "A value for '%s' was not specified. Exiting." % failed_value
	sys.exit (42)

def checkLogin (scan_page):
    """ Check whether the login was successful. Quits the program if the login
        was not successful """
    pattern = re.compile ("Incorrect User Name/Password.")
    match = pattern.search (scan_page)
    if match:
        print >> sys.stderr, "Incorrect User Name/Password. Exiting."
        sys.exit (42)
    return True

def storeClosed (scan_page):
    """ Checks to see if the local Domino's store is closed.
        Quits the program if it is closed """
    pattern = re.compile ('Store Currently Closed')
    match = pattern.search (scan_page)
    if match:
        print "Your local Domino's store is currently closed. Exiting."
        sys.exit (42)
    return False

def dumpPage (page):
    page_out = None
    with open('dumped_page.html', 'w') as page_out:
        page_out.write(page)

    if page_out:
        page_out.close ()


#####################################################################
#                                                                   #
#    Main Function Flow (Gets Pages, Add Items, Output, Read Conf)  #
#                                                                   #
#####################################################################


def getLoginPage ():
    """ Only needed to get the necessary cookie data """
    print "Getting login page..."
    newpage = getPage (LOGIN_URL)
    return newpage

def getLoginInfo ():
    """ Take input for the username and password needed to login to the Domino's site """
    print "Enter your username:",
    username = raw_input ()
    password = getpass ("Enter your password: ")
    return [username, password]

def Login (current_page, username, password):
    """ Login to the Domino's site """
    formdata = getFormData (current_page, "login")

    setFormField (formdata, 'login:usrName', username)
    setFormField (formdata, 'login:passwd', password)
    setFormField (formdata, 'login:_idcl', 'login:submitLink')

    print "Logging in as %s..." % username

    newpage = getPage (LOGIN_URL, formdata)
    checkLogin (newpage)
    return newpage

def getPizzaPage (current_page):
    """ Gets the promo page

    TODO(rnk): This page doesn't seem to exist for me.
    """
    formdata = getFormData (current_page, "startOrder")

    setFormField (formdata, 'startOrder:_idcl', 'startOrder:formSubmitLink')
    setFormField (formdata, 'goTo', 'NEXT')
    # Needed for me since no Domino's store delivers to me
    #setFormField (formdata, 'startOrder:deliveryOrPickup', 'Pickup')

    newpage = getPage (CHOOSE_PIZZA_URL, formdata)
    storeClosed (newpage)
    return newpage

def startBuildPizza (current_page):
    """ Gets the page that holds the main form for specifying a pizza """
    formdata = getFormData (current_page, "choose_pizza")

    setFormField (formdata, 'choose_pizza:_idcl', 'choose_pizza:goToBuildOwn')
    newpage = getPage (BUILD_PIZZA_URL, formdata)
    return newpage

def addPizza (current_page, pizza, check_coupon=''):
    """ Add the user's custom pizza onto the order """
    formdata = getFormData (current_page, "build_own")

    # Delete any unknown toppings
    formdata_temp = formdata.copy ()
    topping_re = re.compile (r"topping(?!Side|Amount).*")
    temp_topping_keys = [value["cryptic_name"] for key, value in toppings_dict.iteritems ()]
    for key, value in formdata_temp.iteritems ():
        # If key is cheese or sause, skip
        if key == TOPPING_CHEESE or key == TOPPPING_SAUSE:
            continue
        elif topping_re.match (key) and key not in temp_topping_keys:
            del formdata[key]
    del formdata_temp

    for i, topping in enumerate (toppings_long):
        if pizza.order[topping][0] != "N":
            # Check that topping exists in pizza form
            if toppings_dict[topping]["cryptic_name"] not in formdata:
                raise Exception ("Selected topping \"%s\" (%s) does not exist in form.\nCurrent form: %s" % (topping, toppings_dict[topping]["cryptic_name"], formdata))

            setFormField (formdata, toppings_dict[topping]["cryptic_num"], pizza.order[topping][0]) # Fill field with topping settings
        else:
            # Unused toppings must be removed from form data
            topping_field = toppings_dict[topping]["cryptic_name"]
            if topping_field in formdata: del formdata[topping_field]

    setFormField (formdata, "builderCrust", pizza.order["crust"])
    setFormField (formdata, "builderSize", pizza.order["size"])
    setFormField (formdata, "builderQuantity", pizza.order["quantity"])
    setFormField (formdata, "build_own:_idcl", "build_own:doAdd")
#    print formdata

    newpage = getPage (ADD_PIZZA_URL, formdata)
    return newpage

def calculateTotal ():
    """ Gets the total for an order. Needed to run prior to
        going to the confirmation page or the total cannot be obtained
        due to the use of AJAX """
    newpage = getPage (CALCULATE_TOTAL_URL, CALCULATE_TOTAL_URL_POST_VARS)
    a = dom.parseString (newpage)
    order_total = a.getElementsByTagName ('total')[0].firstChild.data
    return order_total

def getSidesPage (current_page, check_coupon=''):
    """ Gets the sides page """
    formdata = getFormData (current_page, "build_own")

    setFormField (formdata, 'build_own:_idcl', 'build_own:tab3')
#    print formdata

    newpage = getPage (ADD_SIDES_URL, formdata)
    return newpage

def getConfirmationPage (current_page):
    """ Gets the confirmation page """
    formdata = getFormData (current_page, "orderSummaryForm")

    setFormField (formdata, 'orderSummaryForm:_idcl', 'orderSummaryForm:osCheckout')
    newpage = getPage (CHECKOUT_URL, formdata)
    return newpage

def submitFinalOrder (current_page, total, check_force):
    """ Submits the final order to Domino's """
    choice = ""
    if not check_force:
        print "Confirmation: order for %s (y|yes|n|no)?" % (total),
        choice = raw_input ()
    if check_force or choice.lower () == 'y' or choice.lower () == 'yes':
        formdata = getFormData (current_page, "pricingEnabled")
        setFormField (formdata, 'pricingEnabled:_idcl', 'pricingEnabled:placeOrdeLinkHIDDEN')

        print "Checking out for your order of %s..." % total
        # Sends the final order data to Domino's. After this point,
        # the order is complete. Comment the getPage line below if you want
        # to test the entire program, including this function,
        # without submitting the final order
        #newpage = getPage (SUBMIT_ORDER_URL, formdata)
        return True
    elif choice.lower () == 'n' or choice.lower () == 'no':
        return False
    else:
        raise Exception ("You made an invalid choice.")

def Logout ():
    """ Logs the user off of the site """
    print "Logging out..."
    page = getPage (LOGOUT_URL)

def outputOrder (pizza):
    """ Outputs the current order in a readable format """
    print "%s %s, %s" % (pizza.quantity, pizza.size, pizza.crust),

    length = len (pizza.toppings)

    if pizza.quantity > 1 and length > 0:
        print "pizzas with",
    elif pizza.quantity > 1:
        print "pizzas..."
    elif length > 0:
        print "pizza with",
    else:
        print "pizza..."

    for i, topping in enumerate (pizza.toppings):
        topping = topping.replace ('-', ' ') # Use space when printing topping name

        if length > 2 and (length - i) >= 2:
            print "%s," % topping,
        elif length == 1:
            print "%s..." % topping
        # Used to print first of two toppings
        elif (length - i) == 2:
            print "%s" % topping,
        else:
            print "and %s..." % topping


def parseArguments (command_list, cur_pizza, skip_flags=False):
	""" Parses any command-line arguments or arguments from a batch file """
	username = ""
	password = ""
	coupon = ""
	force = False
	login = False
	input_file = ""

	short_commands = "".join (toppings)
	short_commands += "U:P:O:FLI:H"
	long_commands = []
	long_commands.extend (toppings_long)
	long_commands.extend (["username=", "password=", "coupon=", "force", "input-file=", "login", "help"])

	try:
		opts, args = getopt.getopt (command_list, short_commands, long_commands)
	except getopt.GetoptError, [msg, opt]:
		print >> sys.stderr, "Invalid argument passed: %s" % opt
		print >> sys.stderr, "Displaying help text and quitting"
		displayHelp ()
		sys.exit(42)

	# Parse regular options
	for opt, arg in opts:
		if opt.strip ('-') in toppings:
			topping = opt.strip ('-')
			cur_pizza.setTopping (topping)
		elif opt.strip ('--') in toppings_long:
			topping = opt.strip ('--')
			cur_pizza.setTopping (topping)
		elif opt in ("-U", "--username"):
			if not skip_flags:
				username = arg
		elif opt in ("-P", "--password"):
			if not skip_flags:
				password = arg
		elif opt in ("-O", "--coupon"):
			if not skip_flags:
				coupon = arg
		elif opt in ("-F", "--force"):
			if not skip_flags:
				force = True
		elif opt in ("-I", "--input-file"):
			if not skip_flags:
				input_file = arg
		elif opt in ("-L", "--login"):
			if not skip_flags:
				login = True
		elif opt in ("-H", "--help"):
			if not skip_flags:
				displayHelp ()
				sys.exit (42)

	# Parse positional arguments
	for argument in args:
		if argument in sizes:
			cur_pizza.setSize (argument)
		elif argument in crusts:
			cur_pizza.setCrust (argument)
		elif argument.isdigit ():
			cur_pizza.setQuantity (argument)
		else:
			print >> sys.stderr, "'%s' is not a valid argument. Exiting." % argument
			sys.exit (42)

	if not skip_flags:
		return [username, password, coupon, force, login, input_file]


def displayHelp ():
    """ Print the help menu """
    print
    print "Pizza Py Party %s" % VERSION_NUM
    print "Usage: pizza-py-party [OPTIONS] [TOPPINGS] [QUANTITY] [SIZE] [CRUST]"
    print
    print "QUANTITY can be between %s and %s. No more than %s pizzas can be ordered." % (MIN_QTY, MAX_QTY, MAX_TOTAL_QTY)
    print "SIZE can be: small, medium, large, or x-large."
    print "Note: small is not available for deepdish or brooklyn."
    print "      medium is not available for brooklyn"
    print "      x-large is not available for deepdish, thin."
    print "CRUST can be: handtoss, deepdish, thin, or brooklyn."
    print
    print "Example: `pizza-py-party -pmd 2 medium thin` orders 2 medium,\nthin pizzas with pepperoni, mushrooms, and cheedar cheese."
    print
    print "Options are:"
    print "  -U, --username <USERNAME>        Specify your user name"
    print "  -P, --password <PASSWORD>        Specify your password"
    print "  -O, --coupon   <ID# | x>         Specify an online coupon. Input x to \n",
    print "                                   see the coupon menu"
    print "  -F, --force                      Order the pizza with no user confirmation"
    print "  -I, --input-file <BATCHFILE>     Input file to read batch of pizza\n",
    print "                                   (see man page for info)"
    print "  -L, --login                      Specify login information within the \n",
    print "                                   program as opposed to using the command \n",
    print "                                   line arguments"
    print "  -H, --help                       Display help text"
    print
    print "Toppings are:"
    for topping in toppings_long:
        current = toppings_dict[topping]
        print "  -%(short)s, --%(long)s %(help)s" % {'short': current['short'], 'long': current['long'], 'help': current['help_text']}
    print
    print "See the man page for more details on accounts, configuration files,\nand batch ordering.\n"

def getCouponsPage (current_page):
    """ Gets the coupon page """
    formdata = getFormData (current_page, "choose_pizza")

    setFormField (formdata, 'choose_pizza:_idcl', 'choose_pizza:couponsButton')
    #setFormField (formdata, 'goTo', 'COUPONS')

    #setFormField (formdata, 'startOrder:_idcl', 'startOrder:formSubmitLink')
    #setFormField (formdata, 'goTo', 'COUPONS')
    # Needed for me since no Domino's store delivers to me
    #setFormField (formdata, 'startOrder:deliveryOrPickup', 'Pickup')

#    newpage = getPage (COUPON_PAGE_URL, formdata)
    newpage = getPage (ADD_COUPON_URL, formdata)
    storeClosed (newpage)
    dumpPage (newpage)
    return newpage

def getAvailableCoupons (current_page):
    """ Calls the ParseCoupons class to obtain the available coupon offers """
    parsed_page = ParseCoupons ()
    parsed_page.feed (current_page)
    parsed_page.close ()
    return parsed_page.formdata

def printAvailableCoupons (coupon_data):
    """ Print the available coupon offers """
    print
    print "Coupon Menu"
    print "----------------"
    print
    for id, desc, price in coupon_data:
        print "Coupon ID#: %s" % id
        print "Description: %s" % desc
        if not price:
            price = "Read description for details"
        print "Price: %s" % price
        print
    print
    print """Coupon offers are not validated within this program so make sure
to pick a proper order for the coupon you use. Also, coupon offers
are subject to change so be cautious if using this program
with a coupon offer under cron."""

def addCoupon (current_page, coupon, coupon_data):
    """ Add the coupon code to the user's order """
    formdata = getFormData (current_page, "couponsForm")

    # Take the coupon_data list, place the coupon ids in a temporary list,
    # and find out if the coupon code specified is valid
    temp = []
    for id, desc, price in coupon_data:
        temp.append (id)
    if not coupon in temp:
        raise Exception ("'%s' is not a valid coupon code." % coupon)

    setFormField (formdata, 'couponsForm:userCode', coupon)
    setFormField (formdata, 'couponsForm:_idcl', 'couponsForm:addUserCouponCP')

    newpage = getPage (ADD_COUPON_URL, formdata)
    return newpage

def readConfFile ():
	""" Parse the configuration file, if it exists,
	    and return the values obtained """
	home = os.path.expanduser("~")
	path = os.path.join (home, ".pizza-py-party.conf")
	default_username = ""
	default_password = ""
	default_quantity = ""
	default_size = ""
	default_crust = ""
	default_toppings = []
	if not os.path.isfile (path):
		return False
	file = open (path, 'r')
	readline = file.readline ()
	while readline:
		if readline.startswith ("username="):
			c, parsedline = readline.split ("username=")
			default_username = parsedline.strip ()
		elif readline.startswith ("password="):
			c, parsedline = readline.split ("password=")
			default_password = parsedline.strip ()
		elif readline.startswith ("default_quantity="):
			c, parsedline = readline.split ("default_quantity=")
			default_quantity = parsedline.strip ()
		elif readline.startswith ("default_size="):
			c, parsedline = readline.split ("default_size=")
			default_size = parsedline.strip ()
		elif readline.startswith ("default_crust="):
			c, parsedline = readline.split ("default_crust=")
			default_crust = parsedline.strip ()
		elif readline.startswith ("default_toppings="):
			c, parsedline = readline.split ("default_toppings=")
			parsedline = parsedline.strip ()
			parsedline = parsedline.split ()
			default_toppings = parsedline
		elif readline.startswith ('#'):
			readline = file.readline ()
			continue
		elif readline.strip() == '':
			readline = file.readline ()
			continue
		else:
			print >> sys.stderr, "Invalid line has been detected. \n\"%s\" \nExiting." % readline.strip()
			sys.exit (42)
		readline = file.readline ()

	return [default_username, default_password, default_crust, default_size, default_quantity, default_toppings]

def parseBatchFile (batchfile):
	""" Parse the specified batch file and return a list of the lines read """
	if not os.path.isfile (batchfile):
		print "The input file does not exist. Exiting."
		sys.exit (42)
	pizza_lines = []
	file = open (batchfile, 'r')
	readline = file.readline ()
	while readline:
		if readline.startswith ('#'):
			readline = file.readline ()
			continue
		elif readline.strip () == '':
			readline = file.readline ()
			continue
		else:
			readline = readline.strip ()
			newline = readline.split ()
			pizza_lines.append (newline)
		readline = file.readline ()
	return pizza_lines


###########################################################
#                                                         #
#                    Primary Program                      #
#                                                         #
###########################################################


def main (argv):
    # Assign default lists and a default Pizza object
    pizza_list = []
    pizza_commands = []
    pizza = Pizza ()

    # Parse command-line arguments
    username, password, coupon, force, login, input_file = parseArguments (argv[1:], pizza)

    # If a pizza was defined in the command-line arguments, add it to the pizza
    # list. Else, delete the initial Pizza object
    if pizza.crust or pizza.size or pizza.quantity or pizza.toppings:
        pizza_list.append (pizza)
    else:
        del pizza

    # If a batch file was specified on the command-line,
    # parse it and store the result in a list
    if input_file:
        pizza_commands = parseBatchFile (input_file)

    # Parse the arguments found in the batch file and add any
    # pizzas to the pizza list. Will be skipped if no batch
    # file was specified
    for arguments in pizza_commands:
        pizza = Pizza ()
        parseArguments (arguments, pizza, True)
        pizza_list.append (pizza)

    # Only allow interactive login if no value has been
    # specified for the username or password
    if not username and not password and login:
        username, password = getLoginInfo ()
        print

    # Parse the config file if one exists
    parsed_conf = readConfFile ()
    if parsed_conf:
        # If a pizza has not been defined and a config file was parsed,
        # add a blank Pizza object to the list and check for any default values
        if len (pizza_list) == 0:
            pizza = Pizza ()
            pizza_list.append (pizza)
        # Merge the default config attributes with the pizzas in the list
        for pizza in pizza_list:
            username, password = mergeAttributes (parsed_conf, username, password, pizza)

    # If no pizzas have been specified in any way and the user is
    # not going to see the coupon menu,
    # tell the user about the problem and exit the program
    if len (pizza_list) == 0 and not coupon.lower() == 'x':
        print "You have not selected any pizzas. Exiting."
        sys.exit (42)

    # Check that the username and password have been specified
    # if the user wants to check out the coupon menu
    if coupon.lower() == 'x':
        if not username or not password:
            temp_list = [username, password]
            findMissingAttributes (temp_list)
    else:
        # If a necessary variable has not been defined, find the first undefined
        # variable and exit the program
        for pizza in pizza_list:
            if (not username or not password or not pizza.crust or
                not pizza.size or not pizza.quantity):
                temp_list = [username, password, pizza.crust, pizza.size, pizza.quantity]
                findMissingAttributes (temp_list)

    # Output the user order in a readable form. Skip this section
    # if the user wants to see the coupon menu
    if not coupon.lower() == 'x':
        print "Order: ",
        i = 0
        for pizza in pizza_list:
            if i > 0:
                print "       ",
            outputOrder (pizza)
            i += 1
        print

    # Get login page (required to get primary cookie)
    page = getLoginPage ()

    # Go to Step 1 section (Account Page)
    page = Login (page, username, password)
    username = ""
    password = ""

    if coupon and coupon.lower() == 'x':
        # Get coupons page, print the available coupons, and exit
        page = getCouponsPage (page)
        coupon_data = getAvailableCoupons (page)
        printAvailableCoupons (coupon_data)
        sys.exit ()
    elif coupon:
        # Get coupons page, parse available coupons,
        # and add the coupon if the coupon code exists
        page = getCouponsPage (page)
        coupon_data = getAvailableCoupons (page)
        page = addCoupon (page, coupon, coupon_data)
    else:
        # Go to Step 2 section and get pizza form
        try:
            page = getPizzaPage (page)
        except:
            pass  # TODO(rnk): This page doesn't exist for me.
        page = startBuildPizza (page)

    # Add the specified pizza to the order
    for pizza in pizza_list:
        page = addPizza (page, pizza, coupon)

    # Go to Step 3 section (Choose Sides/Drinks section)
    page = getSidesPage (page, coupon)

    # Calculate order total
    order_total = calculateTotal ()

    # Go to Step 4 section (Confirm Order section)
    page = getConfirmationPage (page)

    # Show the order for the final confirmation
    pizza_list_length = len (pizza_list)
    if pizza_list_length == 1:
        print "Submitting order for",
    else:
        print "Submitting order for:"
    for pizza in pizza_list:
        if pizza_list_length != 1:
                print "  ",
        outputOrder (pizza)

    # Prompt the user to confirm the order. Exit the program
    # if the user chooses no
    if not submitFinalOrder (page, order_total, force):
        print "Exiting."
        sys.exit ()

    # Logout and go to the home page
    Logout ()

    print
    print "You should receive a copy of your receipt in your email shortly."


if __name__ == "__main__":
    main (sys.argv)