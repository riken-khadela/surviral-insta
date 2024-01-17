
import requests, re

GETSMSCODE_COUNTRY = "kn"
GETSMSCODE_COUNTRY = "ph"
GETSMSCODE_COUNTRY = "id"

class phone_numbers():
    """
    if dont need chines number then you can just call the function to work with numbers with providing country code otherwise dont need to give country code
    
    ## username and api key
    username = "pay@noborders.net"
    GETSMSCODE_API_KEY = "cfca2f0dd0be35a82de94e038ad2a7e8"
    
    ## project id :
    GETSMSCODE_PID = "8"
    
    ##  kenya, philipines and indonesia country code :
    GETSMSCODE_COUNTRY = "kn"
    GETSMSCODE_COUNTRY = "ph"
    GETSMSCODE_COUNTRY = "id"
    """
    
    def __init__(self,username = "pay@noborders.net",GETSMSCODE_API_KEY = "cfca2f0dd0be35a82de94e038ad2a7e8",GETSMSCODE_PID = "8") :
        self.username = username
        self.GETSMSCODE_API_KEY = GETSMSCODE_API_KEY
        self.GETSMSCODE_PID = GETSMSCODE_PID
    

    
            
    def get_number(self,china = True,country_code=''):
        """
        # for china
        # url = f"http://api.getsmscode.com/do.php?action=getmobile&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}"
        
        # for other country
        url = f"http://api.getsmscode.com/vndo.php?action=getmobile&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&cocode={self.country_code}"
        """
        if country_code : self.country_code = country_code       
        if not china :
            self.get_number_url = f"http://api.getsmscode.com/vndo.php?action=getmobile&username={self.username}&token={self.GETSMSCODE_API_KEY}&pid={self.GETSMSCODE_PID}&cocode={self.country_code}"
        else : 
            self.get_number_url = f"http://api.getsmscode.com/do.php?action=getmobile&username={self.username}&token={self.GETSMSCODE_API_KEY}&pid={self.GETSMSCODE_PID}"
            
        while True:
            payload={}
            headers = {}
            print(f'Get Number usl : {self.get_number_url}')
            response = requests.request("POST", self.get_number_url, headers=headers, data=payload)
            if str(response) == 'Message|Capture Max mobile numbers,you max is 5':
                continue
            else:
                self.phone_number_ = response.text
                break
        return response.text

    def get_sms(self,phone_number,country_code='',china = True):
        """
        # for china
        # url = f"http://api.getsmscode.com/do.php?action=getsms&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&mobile={phone_number}&author=pay@noborders.net"
        
        # other country url
        # url = f"http://api.getsmscode.com/vndo.php?action=getsms&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&mobile={phone_number}&author=pay@noborders.net&cocode={country_code}"
        """
        if country_code : self.country_code = country_code
        self.phone_number = phone_number
        if not china :
            self.get_sms_url = f"http://api.getsmscode.com/vndo.php?action=getsms&username={self.username}&token={self.GETSMSCODE_API_KEY}&pid={self.GETSMSCODE_PID}&mobile={self.phone_number_}&author={self.username}&cocode={self.country_code}"
        else : 
            self.get_sms_url = f"http://api.getsmscode.com/do.php?action=getsms&username={self.username}&token={self.GETSMSCODE_API_KEY}&pid={self.GETSMSCODE_PID}&mobile={self.phone_number_}&author={self.username}"
            
        # if country_code : self.country_code = country_code
        
        print(f'Get Number Message : {self.get_sms_url}')
        response = requests.post(url=self.get_sms_url)
        if response.status_code == 200:
            response_text = response.text
            print(response_text,"response_text----------------------------")
            if 'insta' in (response_text).lower():
                if '|' in (response_text).lower():
                    match = response_text.split('|')
                    print(response_text)
                    message = match[1]
                    code = re.search(r"\d{3}\s*\d{3}", message).group().replace(" ", "")
                    return code
                else:
                    response = response_text.split(' ')
                    otp = response[1]+response[2]
                    return otp


    def ban_number(self,phone_number,country_code,china = True):
        """
        # for china
        # url = f"http://api.getsmscode.com/do.php?action=addblack&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&mobile={phone_number}&author=pay@noborders.net"
        
        # for other counrty
        # url = f"http://api.getsmscode.com/vndo.php?action=addblack&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&mobile={phone_number}&author=pay@noborders.net&cocode={country_code}"
        """
        
        if country_code : self.country_code = country_code
        self.phone_number = phone_number
        
        if not china :
            self.banned_url = f"http://api.getsmscode.com/vndo.php?action=addblack&username={self.username}&token={self.GETSMSCODE_API_KEY}&pid={self.GETSMSCODE_PID}&mobile={self.phone_number_}&author={self.username}&cocode={self.country_code}"
        else : 
            self.banned_url = f"http://api.getsmscode.com/do.php?action=addblack&username={self.username}&token={self.GETSMSCODE_API_KEY}&pid={self.GETSMSCODE_PID}&mobile={self.phone_number_}&author={self.username}"
            
        print(f'Banned Number : {self.banned_url}')
        response = requests.post(url=self.banned_url)
        print(response.text)
        return response

