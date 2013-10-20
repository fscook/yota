import re
from yota.exceptions import NotCallableException
import pysistor
import pickle


class MinLength(object):
    """ Checks to see if data is at least length long.

    :param length: The minimum length of the data.
    :type length: integer

    :param message: The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message", "min_length"]

    def __init__(self, length, message=None):
        self.min_length = length
        self.message = message if message else "Minimum allowed length {0}" \
            .format(length)
        super(MinLength, self).__init__()

    def __call__(self, target):
        if len(target.data) < self.min_length:
            target.add_error({'message': self.message})


class MaxLength(object):
    """ Checks to see if data is at most length long.

    :param length: The maximum length of the data.
    :type length: integer

    :param message: The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message", "max_length"]

    def __init__(self, length, message=None):
        self.max_length = length
        self.message = message if message else "Maximum allowed length {0}" \
            .format(length)
        super(MaxLength, self).__init__()

    def __call__(self, target):
        if len(target.data) > self.max_length:
            target.add_error({'message': self.message})


class NonBlockingDummy(object):
    """ A dummy class for testing non-blocking validators
    """

    def __call__(self, target):
        target.add_error({'message': "I'm not blocking!", 'block': False})


class Matching(object):
    """ Checks if two nodes values match eachother. The error is delivered to
    the first node.

    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message"]

    def __init__(self, message=None):
        self.message = message if message else "Fields must match"
        super(Matching, self).__init__()

    def __call__(self, target1, target2):
        if target1.data != target2.data:
            target1.add_error({'message': self.message})
            target2.add_error({'message': self.message})


class Integer(object):
    """ Checks if the value is an integer and converts it to one if it is

    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message"]

    def __init__(self, message=None):
        self.message = message if message else "Value must only contain numbers"
        super(Integer, self).__init__()

    def __call__(self, target):
        try:
            int(target.data)
        except ValueError:
            target.add_error({'message': self.message})


class MinMax(object):
    """ Checks if the value is between the min and max values given

    :param message: (optional) The message to present to the user upon failure.
    :type message: string

    :param min: The minimum length of the data.
    :type length: integer

    :param max: The maximum length of the data.
    :type length: integer
    """
    __slots__ = ["minmsg", "maxmsg", "max", "min"]

    def __init__(self,
                 min,
                 max,
                 minmsg=None,
                 maxmsg=None):
        self.min = min
        self.max = max
        self.minmsg = minmsg if minmsg else "Must be longer than {0} characters".format(min)
        self.maxmsg = maxmsg if maxmsg else "Must be fewer than {0} characters".format(max)
        super(MinMax, self).__init__()

    def __call__(self, target):
        if len(target.data) < self.min:
            target.add_error({'message': self.minmsg})
        if len(target.data) > self.max:
            target.add_error({'message': self.maxmsg})


class Regex(object):
    """ Quick and easy check to see if the input
    matches the given regex.

    :param regex: (optional) The regex to run against the input.
    :type regex: string
    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message", "regex"]

    def __init__(self, regex=None, message=None):
        self.message = message if message else "Input does not match regex"
        self.regex = regex
        super(Regex, self).__init__()

    def __call__(self, target=None):
        if re.match(self.regex, target.data) is None:
            target.add_error({'message': self.message})

class Password(Regex):
    """ Quick and easy check to see if a field
    matches a stamdard password regex. This regex
    matches a string at least 7 characters long which
    contains an upper and lowercase letter, a special
    character, a number, and no blanks/returns.

    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message"]

    def __init__(self, message=None):
        self.message = message if message else "Must be 7 characters or longer, contain " \
                                               "at least one upper and lower case letter, " \
                                               "a number, a special character, and no spaces"
        self.regex = '^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=])(?=\S+$).{7,}$'

class Username(Regex):
    """ Quick and easy check to see if a field
    matches a stamdard username regex. This regex
    matches a string from 3-20 characters long and
    composed only of numbers, letters, hyphens, and
    underscores.

    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message"]

    def __init__(self, message=None):
        self.message = message if message else "Must be 3-20 characters and only " \
                                               "contain letters, numbers, hyphens and underscores"
        self.regex = '^[a-zA-Z0-9-_]{3,20}$'


class URL(Regex):
    """ A way to check for a valid URL value """
    __slots__ = ["message", "regex"]

    def __init__(self, message=None):
        self.message = message if message else "Must be 3-20 characters and only " \
                                               "contain letters, numbers, hyphens and underscores"
        self.regex = ('^(?:http|ftp)s?://' # http:// or https://
                        '(?:(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+(?:[A-Za-z]{2,6}\.?|[A-Za-z0-9-]{2,}\.?)|' #domain...
                        'localhost|' #localhost...
                        '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                        '(?::\d+)?' # optional port
                        '(?:/?|[/?]\S+)$')


class PasswordStrength(object):
    """ A validator to check the password strength.

    :param regex: (optional) The regex to run against the input.
    :type regex: list
    :param message: (optional) The message to present to the user upon failure.
    :type message: string

    """
    __slots__ = ["message", "regex"]

    def __init__(self, regex=None, message=None):
        self.message = message
        if not isinstance(regex, list):
            self.regex = [
                "(?=.*[A-Z].*[A-Z])",  # Matches 2 uppercase letters
                "(?=.*[!@#$&%*])",  # Matches 1 Special character
                "(?=.*[0-9].*[0-9])",  # Matches 2 numbers
                ".{7}"  # Has at least 7 characters
             ]
        else:
            self.regex = regex
        super(PasswordStrength, self).__init__()

    def __call__(self, target=None):
        strength = 0

        # Loop through the regex and increment
        # strength for each successful match
        for regex in self.regex:
            if re.match(regex, target.data):
                strength += 1
        target.add_error({'message': "Password strength is " + str(strength),
                          'block': False})


class Captcha(object):
    """ Only validates captcha nodes. Used to check correct solution
    """
    __slots__ = ["message"]

    def __init__(self, message=None):
        self.message = message if message else "Captcha did not match!"
        super(Captcha, self).__init__()

    def __call__(self, target):
        # Fetch the test object from pysistor
        test = pysistor.Pysistor.get("captcha_{0}".format(target.captcha_id),
                              backend=target._parent_form.pysistor_backend,
                              adapter=target._parent_form.pysistor_adapter)
        test = pickle.loads(test)
        if not test.test_solutions([target.data]):
            target.add_error({'message': self.message})


class Required(object):
    """ Checks to make sure the user entered something.

    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    """
    __slots__ = ["message"]

    def __init__(self, message=None):
        self.message = message if message else "A value is required"
        super(Required, self).__init__()

    def __call__(self, target=None):
        if len(target.data) == 0:
            target.add_error({'message': self.message})

class MimeType(object):
    """ Checks to make sure a posted file is an allowed mime type

    :param message: (optional) The message to present to the user upon failure.
    :type message: string
    :param mimetypes: MIME types to check the post against ala 'image/jpeg'
    :type mimetypes: list
    """
    __slots__ = ["message", "mimetypes"]

    def __init__(self, mimetypes, message=None):
        self.mimetypes = mimetypes
        self.message = message if message else "Sorry, that MIME type is not supported"
        super(MimeType, self).__init__()

    def __call__(self, target=None):
        if not target.data.type in self.mimetypes:
            target.add_error({'message': self.message})

class Email(object):
    """ A direct port of the Django Email validator. Checks to see if an
    email is valid using regular expressions.
    """

    user_regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"$)',
        # quoted-string
        re.IGNORECASE)
    domain_regex = re.compile(
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?$)'  # domain
        # literal form, ipv4 address (SMTP 4.1.3)
        r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
        re.IGNORECASE)
    domain_whitelist = ['localhost']

    def __init__(self, message=None):
        self.message = message if message else "Entered value must be a valid"\
                                               " email address"
        super(Email, self).__init__()

    def valid(self, value):
        """ A small breakout function to make passing back errors less
        redundant.
        """
        if not value or '@' not in value:
            return False

        user_part, domain_part = value.rsplit('@', 1)
        if not self.user_regex.match(user_part):
            return False

        if (not domain_part in self.domain_whitelist and
                not self.domain_regex.match(domain_part)):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                if not self.domain_regex.match(domain_part):
                    return False
                else:
                    return True
            except UnicodeError:
                return False

        return True

    def __call__(self, target):
        if self.valid(target.data):
            return None
        else:
            target.add_error({'message': self.message})


class ActionWrapper(object):
    """ A base class for Check and Listener. Both are very similar in operation
    since they are both wrappers around called functions. Their primary
    function is to resolve arguments lazily, allowing validators to be added
    for fields that don't exist. """

    def __init__(self, callable, *args, **kwargs):
        self.callable = callable
        if not args:
            self.args = []
        else:
            self.args = list(args)

        if not kwargs:
            self.kwargs = {}
        else:
            self.kwargs = kwargs

        self._attr_name = None
        self.resolved = False

    def resolve_attr_names(self, form):
        """ Called internally by the validation methods this resolves all arg
        and kwarg strings to their respective `Node` objects and replaces them
        with a KeyedTuple containing the submitted data and the Node object
        reference.
        :param form: A reference to the Form class that the check is being
        resolved to.
        :param data: The full form data dictionary submitted for validation.
        """
        if self.resolved:
            return

        # Process args
        for key, arg in enumerate(self.args):
            self.args[key] = form.get_by_attr(arg)

        # Process kwargs
        for key, val in self.kwargs.items():
            self.kwargs[key] = form.get_by_attr(val)

        self.resolved = True

    def __call__(self):
        """ Called by the validation routines. Allows the Check to specify
        parameters that will be passed to our Validation method.
        """

        if not self.resolved:
            raise ValueError("Check args are not resolved. This should not happen")

        try:
            # Run our validator
            return self.callable(*self.args, **self.kwargs)
        except TypeError as e:
            raise NotCallableException(
                "Validators provided must be callable, type '{0}'" +
                "instead. Caused by {1}".format(type(self.callable), e))


class Check(ActionWrapper):
    """ This object wraps a validator callable and is intended to be used in
    your `Form` subclass definition.

    :param callable validator: This is required to be a callable object
        that will carry out the actual validation. Many generic validators
        exist, or you can roll your own.

    :param list args: A list of strings, or a single string,
        representing that _attr_name of the `Node` you would like passed
        into the validator. Once a validator is called this string will get
        resolved into the Node object

    :param dict kwargs: Same as args above except it allows passing in node
        information as keyword arguments to the validator callable.

    `Check` objects are designed to be declared in your form subclass.
    """

    def node_visited(self, visited):
        """ Used by piecewise validation to determine if all the Nodes involved
        in the validator have been "visited" and thus are ready for the
        validator to be run """

        if not self.resolved:
            raise ValueError("Check args are not resolved. This should not happen")

        """ Loop through the args. for each node, check if it's represented in
        the visited node list. if it is then then we're good to go"""
        for node in self.args:
            for name in node.get_list_names():
                if name in visited:
                    break
            else:  # if we didn't break, not enough info
                return False

        # Process kwargs
        for node in self.kwargs.values():
            for name in node.get_list_names():
                if name in visited:
                    break
            else:  # if we didn't break
                return False

        # we identified at least one name in each node's collection of names
        return True

    def __iter__(self):
        """ A simple way to make functions accept lists or single elements """
        yield self

    def __repr__(self):
        return "<Check at {0}, args: {1}, kwargs: {2}>".format(id(self), self.args, self.kwargs)


class Listener(ActionWrapper):
    """ The class that wraps actions triggered by events. Essentially this just
    holds reference to a callable along with some metadata and a lazy loader
    for Nodes. The Form._event_lists will contain a collection of these objects
    and are what drives the Form.trigger_event function.

    :param string type: The name of the event to listen to. The callable will be
        executed when the event is triggered.

    :param callable validator: This is required to be a callable object
        that will will be executed when the event of `type` is triggered.

    :param string *args: A list of strings, or a single string,
        representing that _attr_name of the `Node` you would like passed
        into the validator. Once a validator is called this string will get
        resolved into the Node object.

    :param dict **kwargs: Same as args above except it allows passing in node
        information as keyword arguments to the validator callable.

    `Listener` objects are designed to be declared in your form subclass.
    """
    def __init__(self, type, callable, *args, **kwargs):
        # Just add the type attribute that the base doesn't have
        self.type = type
        super(Listener, self).__init__(callable, *args, **kwargs)
