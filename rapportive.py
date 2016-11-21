import urllib2
from xml.dom import minidom
import csv
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('cookie', help='place li_at cookie here', type=str)
parser.add_argument('input', help='input file name', type=str)
parser.add_argument('output', help='output file name', type=str)
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

def name2email(fn, ln, domain):
    list = ["{fn}", '{ln}', '{fn}{ln}', '{fn}.{ln}', '{fi}{ln}', '{fi}.{ln}', '{fn}{li}', '{fn}.{li}', '{fi}{li}',
            '{fi}.{li}', '{ln}{fn}', '{ln}.{fn}', '{ln}{fi}', '{ln}.{fi}', '{li}{fn}', '{li}.{fn}', '{li}{fi}',
            '{li}.{fi}', '{fn}-{ln}', '{fi}-{ln}', '{fn}-{li}', '{fi}-{li}', '{ln}-{fn}', '{ln}-{fi}', '{li}-{fn}',
            '{li}-{fi}', '{fn}_{ln}', '{fi}_{ln}', '{fn}_{li}', '{fi}_{li}', '{ln}_{fn}', '{ln}_{fi}', '{li}_{fn}',
            '{li}_{fi}']
    emails = [];

    fi = fn[0]
    li = ln[0]

    for i in list:
        for a in [("{fn}", fn), ("{ln}", ln), ("{fi}", fi), ("{li}", li)]:
            i = i.replace(a[0], a[1])
        emails.append(i + "@" + domain)
    return emails


def get_oauth(cookie_li_at):
    opener = urllib2.build_opener()
    opener.addheaders.append(('cookie', 'li_at=' + cookie_li_at))
    opener.addheaders.append(('referer', 'https://mail.google.com/mail/u/0/'))
    f = opener.open("https://www.linkedin.com/uas/js/userspace?v=0.0.2000-RC8.53856-1429&apiKey=4XZcfCb3djUl-DHJSFYd1l0ULtgSPl9sXXNGbTKT2e003WAeT6c2AqayNTIN5T1s&onLoad=linkedInAPILoaded612163388635963&authorize=true&credentialsCookie=true&secure=1&")

    for line in f.readlines():
        if "oauth_token" in line:
            return line.split('"')[1]


def check_email_existance(oauth_token, email_list, fn, ln):
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', ''))
    opener.addheaders.append(('oauth_token', oauth_token))
    opener.addheaders.append(('referer', 'https://api.linkedin.com/uas/js/xdrpc.html?v=0.0.2000-RC8.53856-1429'))

    checked = []

    for i in email_list:

        try:
            f = opener.open(
                "https://api.linkedin.com/v1/people/email=" + i + ":(first-name,last-name,public-profile-url)")
        except urllib2.HTTPError as e:
            #print "%s -> False" % i
            checked.append([i, 0])
        else:
            xml_parsed = minidom.parseString(f.read())
            parsed_first_name = xml_parsed.getElementsByTagName('first-name')[0].childNodes[0].nodeValue
            parsed_last_name = xml_parsed.getElementsByTagName('first-name')[0].childNodes[0].nodeValue
            parsed_link = xml_parsed.getElementsByTagName('public-profile-url')[0].childNodes[0].nodeValue

            # False-Positive Check

            v = 2 if parsed_first_name.lower() != fn and parsed_last_name.lower() != ln else 1
            checked.append([i, v, parsed_link])

    return checked

def write_csv(data):
    with open(args.output, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in data:
            if i is None:
                continue
            writer.writerow(i)
        if args.verbose:
            print "\nData written into: %s" % args.output


def beautiful_data(data):
    for i in data:
        if i[1] != 0:
            return [i[0], i[2]]
    return None

def single_credetials_check(row):
    if args.verbose:
        print "checking %s" % row

    fn, ln, domain = row[0], row[1], row[2]

    o_auth = get_oauth(args.cookie)

    if o_auth != "":

        possible_emails = name2email(fn, ln, domain)
        check_emails = check_email_existance(o_auth, possible_emails, fn, ln)

        prettified_data = beautiful_data(check_emails)

        if args.verbose:
            print "Successfully finished for %s.    Extracted:%s" % (row, prettified_data)

        return prettified_data
    else:
        print "Impossible to Obtain Oauth\nFailed to check %s" % row

def check_email_pack():

    csv_file = open(args.input, 'rb')

    csv_rows = csv.reader(csv_file, delimiter=',', quotechar='|')

    general_output = []

    for row in csv_rows:
        general_output.append(single_credetials_check(row))

    csv_file.close()

    write_csv(general_output)

if __name__ == '__main__':
    check_email_pack()
