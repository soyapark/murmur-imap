#!/usr/bin/python
#
# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
     # http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import imaplib
import json
from optparse import OptionParser
import smtplib
import sys
import urllib
import webbrowser
from datetime import datetime, timedelta

class Oauth2():
  # The URL root for accessing Google Accounts.
  GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'

  # Hardcoded dummy redirect URI for non-web apps.
  REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

  # Record when access token is created to check whether it is expired 
  TOKEN_EXPIRED_TIME = None

  def __init__(self):
    REFRESH_TOKEN = None

    
    
    # if options.refresh_token:
    #   response = RefreshToken(options.client_id, options.client_secret,
    #                           options.refresh_token)
    #   print 'Access Token: %s' % response['access_token']
    #   print 'Access Token Expiration Seconds: %s' % response['expires_in']
    # elif options.generate_oauth2_string:
    #   RequireOptions(options, 'user', 'access_token')
    #   print ('OAuth2 argument:\n' +
    #          GenerateOAuth2String(options.user, options.access_token))
    
    # elif options.test_imap_authentication:
    #   RequireOptions(options, 'user', 'access_token')
    #   TestImapAuthentication(options.user,
    #       GenerateOAuth2String(options.user, options.access_token,
    #                            base64_encode=False))
    # elif options.test_smtp_authentication:
    #   RequireOptions(options, 'user', 'access_token')
    #   TestSmtpAuthentication(options.user,
    #       GenerateOAuth2String(options.user, options.access_token,
    #                            base64_encode=False))
    # else:
    #   options_parser.print_help()
    #   print 'Nothing to do, exiting.'
    #   return

  def isExpired(self): 
    if not self.TOKEN_EXPIRED_TIME:
      return True

    if datetime.now() > self.TOKEN_EXPIRED_TIME:
      return True

    return False

  def setExpiredTime(self, inTime):
    TOKEN_EXPIRED_TIME = inTime

  def refresh_token(self, options):
    if not self.isExpired():
      # skip refreshing if it is not yet expired
      return

    response = self.RefreshToken(options['client_id'], options['client_secret'],
                            options['refresh_token'])

    # self.setExpiredTime( datetime.now() + timedelta(seconds=response['expires_in'] - 5) )

    print ('Access Token: %s' % response['access_token'])
    print ('Access Token Expiration Seconds: %s' % response['expires_in'])

    return response

  def generate_oauth2_token(self, options):
    print (options)
    print ('To authorize token, visit this url and copy verification code below:')
    # TODO press any key to route to the website
    print ('  %s' % self.GeneratePermissionUrl(options['client_id']))
    # webbrowser.open(self.GeneratePermissionUrl(options.client_id, options.scope), new=2)

    authorization_code = raw_input('Enter verification code: ')
    response = self.AuthorizeTokens(options['client_id'], options['client_secret'],
                                  authorization_code)

    REFRESH_TOKEN = response['refresh_token']
    self.setExpiredTime( datetime.now() + timedelta(seconds=response['expires_in'] - 5) )

    print ('Refresh Token: %s' % response['refresh_token'])
    print ('Access Token: %s' % response['access_token'])
    print ('Access Token Expiration Seconds: %s' % response['expires_in'])

    return response

  def AccountsUrl(self, command):
    """Generates the Google Accounts URL.
    Args:
      command: The command to execute.
    Returns:
      A URL for the given command.
    """
    return '%s/%s' % (self.GOOGLE_ACCOUNTS_BASE_URL, command)

  def UrlEscape(self, text):
    # See OAUTH 5.1 for a definition of which characters need to be escaped.
    return urllib.quote(text, safe='~-._')


  def UrlUnescape(self, text):
    # See OAUTH 5.1 for a definition of which characters need to be escaped.
    return urllib.unquote(text)


  def FormatUrlParams(self, params):
    """Formats parameters into a URL query string.
    Args:
      params: A key-value map.
    Returns:
      A URL query string version of the given parameters.
    """
    param_fragments = []
    for param in sorted(params.iteritems(), key=lambda x: x[0]):
      param_fragments.append('%s=%s' % (param[0], self.UrlEscape(param[1])))
    return '&'.join(param_fragments)


  def GeneratePermissionUrl(self, client_id, scope='https://mail.google.com/'):
    """Generates the URL for authorizing access.
    This uses the "OAuth2 for Installed Applications" flow described at
    https://developers.google.com/accounts/docs/OAuth2InstalledApp
    Args:
      client_id: Client ID obtained by registering your app.
      scope: scope for access token, e.g. 'https://mail.google.com'
    Returns:
      A URL that the user should visit in their browser.
    """
    params = {}
    params['client_id'] = client_id
    params['redirect_uri'] = self.REDIRECT_URI
    params['scope'] = scope
    params['response_type'] = 'code'
    return '%s?%s' % (self.AccountsUrl('o/oauth2/auth'),
                      self.FormatUrlParams(params))

  def RefreshToken(self, client_id, client_secret, refresh_token):
    """Obtains a new token given a refresh token.
    See https://developers.google.com/accounts/docs/OAuth2InstalledApp#refresh
    Args:
      client_id: Client ID obtained by registering your app.
      client_secret: Client secret obtained by registering your app.
      refresh_token: A previously-obtained refresh token.
    Returns:
      The decoded response from the Google Accounts server, as a dict. Expected
      fields include 'access_token', 'expires_in', and 'refresh_token'.
    """
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    request_url = self.AccountsUrl('o/oauth2/token')

    response = urllib.urlopen(request_url, urllib.urlencode(params)).read()
    return json.loads(response)

  def AuthorizeTokens(self, client_id, client_secret, authorization_code):
    """Obtains OAuth access token and refresh token.
    This uses the application portion of the "OAuth2 for Installed Applications"
    flow at https://developers.google.com/accounts/docs/OAuth2InstalledApp#handlingtheresponse
    Args:
      client_id: Client ID obtained by registering your app.
      client_secret: Client secret obtained by registering your app.
      authorization_code: code generated by Google Accounts after user grants
          permission.
    Returns:
      The decoded response from the Google Accounts server, as a dict. Expected
      fields include 'access_token', 'expires_in', and 'refresh_token'.
    """
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['code'] = authorization_code
    params['redirect_uri'] = self.REDIRECT_URI
    params['grant_type'] = 'authorization_code'
    request_url = self.AccountsUrl('o/oauth2/token')

    response = urllib.urlopen(request_url, urllib.urlencode(params)).read()
    return json.loads(response)

  def GenerateOAuth2String(self, username, access_token, base64_encode=True):
    """Generates an IMAP OAuth2 authentication string.
    See https://developers.google.com/google-apps/gmail/oauth2_overview
    Args:
      username: the username (email address) of the account to authenticate
      access_token: An OAuth2 access token.
      base64_encode: Whether to base64-encode the output.
    Returns:
      The SASL argument for the OAuth2 mechanism.
    """
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if base64_encode:
      auth_string = base64.b64encode(auth_string)
    return auth_string


  def TestImapAuthentication(self, user, auth_string):
    """Authenticates to IMAP with the given auth_string.
    Prints a debug trace of the attempted IMAP connection.
    Args:
      user: The Gmail username (full email address)
      auth_string: A valid OAuth2 string, as returned by GenerateOAuth2String.
          Must not be base64-encoded, since imaplib does its own base64-encoding.
    """
    print
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.debug = 4
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
    imap_conn.select('INBOX')


  def TestSmtpAuthentication(self, user, auth_string):
    """Authenticates to SMTP with the given auth_string.
    Args:
      user: The Gmail username (full email address)
      auth_string: A valid OAuth2 string, not base64-encoded, as returned by
          GenerateOAuth2String.
    """
    print
    smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_conn.set_debuglevel(True)
    smtp_conn.ehlo('test')
    smtp_conn.starttls()
    smtp_conn.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(auth_string))



def SetupOptionParser():
  # Usage message is the module's docstring.
  parser = OptionParser(usage=__doc__)
  parser.add_option('--generate_oauth2_token',
                    action='store_true',
                    dest='generate_oauth2_token',
                    help='generates an OAuth2 token for testing')
  parser.add_option('--generate_oauth2_string',
                    action='store_true',
                    dest='generate_oauth2_string',
                    help='generates an initial client response string for '
                         'OAuth2')
  parser.add_option('--client_id',
                    default=None,
                    help='Client ID of the application that is authenticating. '
                         'See OAuth2 documentation for details.')
  parser.add_option('--client_secret',
                    default=None,
                    help='Client secret of the application that is '
                         'authenticating. See OAuth2 documentation for '
                         'details.')
  parser.add_option('--access_token',
                    default=None,
                    help='OAuth2 access token')
  parser.add_option('--refresh_token',
                    default=None,
                    help='OAuth2 refresh token')
  parser.add_option('--scope',
                    default='https://mail.google.com/',
                    help='scope for the access token. Multiple scopes can be '
                         'listed separated by spaces with the whole argument '
                         'quoted.')
  parser.add_option('--test_imap_authentication',
                    action='store_true',
                    dest='test_imap_authentication',
                    help='attempts to authenticate to IMAP')
  parser.add_option('--test_smtp_authentication',
                    action='store_true',
                    dest='test_smtp_authentication',
                    help='attempts to authenticate to SMTP')
  parser.add_option('--user',
                    default=None,
                    help='email address of user whose account is being '
                         'accessed')
  return parser


  