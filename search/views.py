import requests
import time
import threading
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

API_URL = "https://november7-730026606190.europe-west1.run.app/messages/"
CACHE_KEY = "messages_cache"
CACHE_TIMEOUT = 300
CACHE_REFRESH_THRESHOLD = 240  
BATCH_SIZE = 500 


def fetch_all_messages_in_batches():
    all_messages = []
    skip = 0
    
    try: 
        response = requests.get(f"{API_URL}?skip=0&limit=1", timeout=5)
        response.raise_for_status()
        data = response.json()
        total_count = data.get('total', 0)
        
        while skip < total_count:
            response = requests.get(
                f"{API_URL}?skip={skip}&limit={BATCH_SIZE}", 
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
            
            all_messages.extend(items)
            skip += BATCH_SIZE 
        cache.set(CACHE_KEY, all_messages, CACHE_TIMEOUT, version=1)
        cache.set(f"{CACHE_KEY}_timestamp", time.time(), CACHE_TIMEOUT)
        
        print(f"Successfully cached {len(all_messages)} messages")
        return all_messages
        
    except Exception as e:
        print(f"Failed to fetch messages: {e}") 
        return cache.get(CACHE_KEY, version=1) or []


def _initial_cache(): 
    print("Starting initial cache ")
    fetch_all_messages_in_batches()

_initial_cache()


def get_messages(): 
    cache_data = cache.get(CACHE_KEY, version=1)
    if cache_data is None:
        return fetch_all_messages_in_batches()
    
    cache_age = cache.get(f"{CACHE_KEY}_timestamp")
    current_time = time.time()
    
    if cache_age and (current_time - cache_age) > CACHE_REFRESH_THRESHOLD:
        print("Cache getting old, refreshing in background...")
        thread = threading.Thread(target=fetch_all_messages_in_batches, daemon=True)
        thread.start()
    return cache_data


def search_in_messages(query, messages):
    if not query:
        return messages
    
    query = query.lower()
    results = []
    
    for msg in messages:
        message_text = msg.get('message', '').lower()
        username = msg.get('user_name', '').lower()
        user_id = msg.get('user_id', '').lower()
        
        if query in message_text or query in username or query in user_id:
            results.append(msg)
    
    return results


class SearchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'query': self.request.GET.get('q', ''),
            'results': data,
            'total_count': self.page.paginator.count,
            'page': self.page.number,
            'page_size': len(data),
            'total_pages': self.page.paginator.num_pages
        })


class SearchView(APIView):
    pagination_class = SearchPagination
    def get(self, request):
        start = time.time()
        query = request.GET.get('q', '').strip()
        messages = get_messages()
        
        if not messages:
            return Response(
                {
                    'error': 'Unable to fetch data. Please try again.',
                    'response_time_ms': round((time.time() - start) * 1000, 2)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        filtered = search_in_messages(query, messages)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filtered, request, view=self)
        
        response = paginator.get_paginated_response(page)
        elapsed = round((time.time() - start) * 1000, 2)
        response.data['response_time_ms'] = elapsed
        response.data['total_messages_cached'] = len(messages)
        if elapsed > 80:
            print(f"Slow response: {elapsed}ms for query='{query}'")
        
        return response