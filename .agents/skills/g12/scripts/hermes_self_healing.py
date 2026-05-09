#!/usr/bin/env python3
import json
from datetime import datetime
LOG = '/tmp/g12_sh.json'
TH = 0.7

class SH:
    def __init__(self):
        self.p = []
        self.d = []
        try:
            with open(LOG) as f: o = json.load(f)
            self.p = o.get('problems', [])
            self.d = o.get('decisions', [])
        except: pass
    
    def detect(self, c):
        r = []
        if c.get('b', 0) < 50:
            r.append({'id': 'LB', 'title': '余额不足', 'detail': f"${c.get('b', 0):.2f}", 'sev': 0.8})
        if c.get('s', 0) > 10 and c.get('e', 0) == 0:
            r.append({'id': 'NE', 'title': '有信号无执行', 'detail': f"信号{c.get('s', 0)}个0执行", 'sev': 0.9})
        if c.get('r', 0) < -5:
            r.append({'id': 'NR', 'title': '日收益为负', 'detail': f"{c.get('r', 0):.2f}%", 'sev': 0.7})
        return r
    
    def run(self, ctx):
        print('=' * 50)
        print('G12 Self-Healing')
        print('=' * 50)
        ps = self.detect(ctx)
        print(f'Problems: {len(ps)}')
        for p in ps:
            print(f"  {p['title']}: {p['detail']}")
        self.p.extend(ps)
        self.d.append({'time': datetime.now().isoformat(), 'count': len(ps)})
        with open(LOG, 'w') as f:
            json.dump({'problems': self.p, 'decisions': self.d}, f, indent=2)
        return {'status': 'OK'}

if __name__ == '__main__':
    SH().run({'b': 30, 's': 15, 'e': 0, 'r': -3.5})
