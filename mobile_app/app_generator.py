"""
移动端App生成器 - React Native / Flutter
"""
import json

class MobileAppGenerator:
    """
    移动端App生成器
    生成: iOS/Android 原生代码
    """
    def __init__(self, project_name='QuantMaster'):
        self.project_name = project_name
        self.screens = []
        self.components = {}
        self.api_endpoints = []
        self.navigation = []
    
    def add_screen(self, name, screen_type):
        """添加屏幕"""
        self.screens.append({
            'name': name,
            'type': screen_type
        })
    
    def generate_react_native(self):
        """生成React Native代码"""
        code = '''
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';

// Screens
import DashboardScreen from './screens/Dashboard';
import TradingScreen from './screens/Trading';
import PortfolioScreen from './screens/Portfolio';
import SettingsScreen from './screens/Settings';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Trading" component={TradingScreen} />
      <Tab.Screen name="Portfolio" component={PortfolioScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Main" component={MainTabs} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
'''
        return code
    
    def generate_flutter(self):
        """生成Flutter代码"""
        code = '''
import 'package:flutter/material.dart';

void main() {
  runApp(QuantMasterApp());
}

class QuantMasterApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'QuantMaster',
      theme: ThemeData.dark(),
      home: MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  @override
  _MainScreenState createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  
  final screens = [
    DashboardScreen(),
    TradingScreen(),
    PortfolioScreen(),
    SettingsScreen(),
  ];
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.trending_up), label: 'Trading'),
          BottomNavigationBarItem(icon: Icon(Icons.account_balance_wallet), label: 'Portfolio'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
'''
        return code
    
    def generate_pwa(self):
        """生成Progressive Web App"""
        manifest = {
            "name": "QuantMaster",
            "short_name": "QM",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f0f14",
            "theme_color": "#00d4ff",
            "icons": [
                {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
            ]
        }
        
        service_worker = '''
const CACHE_NAME = 'quantmaster-v1';
const urlsToCache = [
  '/',
  '/static/js/main.js',
  '/static/css/main.css'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
'''
        return {'manifest': manifest, 'service_worker': service_worker}
    
    def generate_restapi_client(self):
        """生成REST API客户端"""
        code = '''
import requests
from typing import Optional, Dict, List

class QuantMasterClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {'X-API-Key': api_key}
    
    def get_status(self) -> Dict:
        return requests.get(f'{self.base_url}/api/v1/status', headers=self.headers).json()
    
    def get_positions(self) -> List[Dict]:
        return requests.get(f'{self.base_url}/api/v1/positions', headers=self.headers).json()
    
    def send_order(self, symbol: str, side: str, qty: float, price: Optional[float] = None) -> Dict:
        data = {'symbol': symbol, 'side': side, 'qty': qty}
        if price:
            data['price'] = price
        return requests.post(f'{self.base_url}/api/v1/orders', json=data, headers=self.headers).json()
    
    def get_performance(self) -> Dict:
        return requests.get(f'{self.base_url}/api/v1/performance', headers=self.headers).json()
    
    def get_signals(self) -> List[Dict]:
        return requests.get(f'{self.base_url}/api/v1/signals', headers=self.headers).json()
'''
        return code

class MobileAPI:
    """移动端API服务"""
    def __init__(self, quant_master_system):
        self.qm = quant_master_system
        self.push_tokens = {}
    
    def register_device(self, user_id, device_token, platform='ios'):
        """注册设备"""
        self.push_tokens[user_id] = {
            'token': device_token,
            'platform': platform
        }
    
    def send_push(self, user_id, title, body, data=None):
        """发送推送"""
        token = self.push_tokens.get(user_id)
        if not token:
            return False
        
        # 平台特定推送
        if token['platform'] == 'ios':
            return self._send_apns(token['token'], title, body, data)
        elif token['platform'] == 'android':
            return self._send_fcm(token['token'], title, body, data)
        return False
    
    def _send_apns(self, token, title, body, data):
        """Apple Push Notification"""
        # 简化实现
        print(f"[Push] APNs to {token[:10]}...: {title}")
        return True
    
    def _send_fcm(self, token, title, body, data):
        """Firebase Cloud Messaging"""
        print(f"[Push] FCM to {token[:10]}...: {title}")
        return True
