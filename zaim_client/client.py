import os
import requests
from requests_oauthlib import OAuth1
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


class ZaimClient:
    """Zaim API Client with OAuth 1.0a authentication"""
    
    BASE_URL = "https://api.zaim.net/v2"
    
    def __init__(self, 
                 consumer_key: Optional[str] = None,
                 consumer_secret: Optional[str] = None,
                 access_token: Optional[str] = None,
                 access_token_secret: Optional[str] = None):
        """
        Initialize Zaim API client
        
        Args:
            consumer_key: OAuth consumer key (or set ZAIM_CONSUMER_KEY env var)
            consumer_secret: OAuth consumer secret (or set ZAIM_CONSUMER_SECRET env var)
            access_token: OAuth access token (or set ZAIM_ACCESS_TOKEN env var)
            access_token_secret: OAuth access token secret (or set ZAIM_ACCESS_TOKEN_SECRET env var)
        """
        self.consumer_key = consumer_key or os.getenv('ZAIM_CONSUMER_KEY')
        self.consumer_secret = consumer_secret or os.getenv('ZAIM_CONSUMER_SECRET')
        self.access_token = access_token or os.getenv('ZAIM_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('ZAIM_ACCESS_TOKEN_SECRET')
        
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            raise ValueError("OAuth credentials are required")
            
        self.auth = OAuth1(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
            signature_method='HMAC-SHA1'
        )
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            # リクエストパラメータを準備
            request_params = {
                'method': method,
                'url': url,
                'auth': self.auth
            }
            
            # GETリクエストの場合はparamsを使用、POST/PUT/DELETEの場合はdataを使用
            if method.upper() == 'GET':
                if params:
                    request_params['params'] = params
            else:
                if data:
                    request_params['data'] = data
                    request_params['headers'] = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            response = requests.request(**request_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def verify_user(self) -> Dict[str, Any]:
        """Verify user authentication"""
        return self._make_request('GET', '/home/user/verify')
    
    def get_money(self, 
                  category_id: Optional[int] = None,
                  genre_id: Optional[int] = None,
                  mode: Optional[str] = None,
                  order: str = 'date',
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None,
                  page: int = 1,
                  limit: int = 20) -> Dict[str, Any]:
        """Get money records"""
        params = {
            'mapping': 1,
            'order': order,
            'page': page,
            'limit': min(limit, 100)
        }
        
        if category_id:
            params['category_id'] = category_id
        if genre_id:
            params['genre_id'] = genre_id
        if mode:
            params['mode'] = mode
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        return self._make_request('GET', '/home/money', params=params)
    
    def create_payment(self, 
                      category_id: int,
                      genre_id: int,
                      amount: int,
                      date: str,
                      from_account_id: Optional[int] = None,
                      comment: Optional[str] = None,
                      name: Optional[str] = None,
                      place: Optional[str] = None) -> Dict[str, Any]:
        """Create payment record"""
        data = {
            'mapping': 1,
            'category_id': category_id,
            'genre_id': genre_id,
            'amount': amount,
            'date': date
        }
        
        if from_account_id:
            data['from_account_id'] = from_account_id
        if comment:
            data['comment'] = comment[:100]
        if name:
            data['name'] = name[:100]
        if place:
            data['place'] = place[:100]
            
        return self._make_request('POST', '/home/money/payment', data=data)
    
    def create_income(self,
                     category_id: int,
                     amount: int,
                     date: str,
                     to_account_id: Optional[int] = None,
                     comment: Optional[str] = None,
                     place: Optional[str] = None) -> Dict[str, Any]:
        """Create income record"""
        data = {
            'mapping': 1,
            'category_id': category_id,
            'amount': amount,
            'date': date
        }
        
        if to_account_id:
            data['to_account_id'] = to_account_id
        if comment:
            data['comment'] = comment[:100]
        if place:
            data['place'] = place[:100]
            
        return self._make_request('POST', '/home/money/income', data=data)
    
    def create_transfer(self,
                       amount: int,
                       date: str,
                       from_account_id: int,
                       to_account_id: int,
                       comment: Optional[str] = None) -> Dict[str, Any]:
        """Create transfer record"""
        data = {
            'mapping': 1,
            'amount': amount,
            'date': date,
            'from_account_id': from_account_id,
            'to_account_id': to_account_id
        }
        
        if comment:
            data['comment'] = comment[:100]
            
        return self._make_request('POST', '/home/money/transfer', data=data)
    
    def update_money(self,
                    record_id: int,
                    record_type: str,
                    amount: int,
                    date: str,
                    **kwargs) -> Dict[str, Any]:
        """Update money record"""
        if record_type not in ['payment', 'income', 'transfer']:
            raise ValueError("record_type must be 'payment', 'income', or 'transfer'")
            
        data = {
            'mapping': 1,
            'amount': amount,
            'date': date
        }
        data.update(kwargs)
        
        return self._make_request('PUT', f'/home/money/{record_type}/{record_id}', data=data)
    
    def delete_money(self, record_id: int, record_type: str) -> Dict[str, Any]:
        """Delete money record"""
        if record_type not in ['payment', 'income', 'transfer']:
            raise ValueError("record_type must be 'payment', 'income', or 'transfer'")
            
        return self._make_request('DELETE', f'/home/money/{record_type}/{record_id}')
    
    def get_categories(self) -> Dict[str, Any]:
        """Get user's categories"""
        return self._make_request('GET', '/home/category', params={'mapping': 1})
    
    def get_genres(self) -> Dict[str, Any]:
        """Get user's genres"""
        return self._make_request('GET', '/home/genre', params={'mapping': 1})
    
    def get_accounts(self) -> Dict[str, Any]:
        """Get user's accounts"""
        return self._make_request('GET', '/home/account', params={'mapping': 1})
    
    def get_default_categories(self) -> Dict[str, Any]:
        """Get default categories"""
        return self._make_request('GET', '/category')
    
    def get_default_genres(self) -> Dict[str, Any]:
        """Get default genres"""
        return self._make_request('GET', '/genre')
    
    def get_default_accounts(self) -> Dict[str, Any]:
        """Get default accounts"""
        return self._make_request('GET', '/account')
    
    def get_currencies(self) -> Dict[str, Any]:
        """Get currency list"""
        return self._make_request('GET', '/currency')