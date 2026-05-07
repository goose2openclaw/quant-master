#!/usr/bin/env python3
"""
XIAMI DeFi Token Creator - 智能代币生成器
支持 ERC-20, BEP-20, SPL (Solana)
"""

import json
import os
from datetime import datetime

class TokenGenerator:
    def __init__(self):
        self.templates = self.load_templates()
        
    def load_templates(self):
        return {
            'erc20': {
                'blockchain': 'Ethereum',
                'standard': 'ERC-20',
                'features': ['mintable', 'burnable', 'pausable']
            },
            'bep20': {
                'blockchain': 'BNB Chain',
                'standard': 'BEP-20', 
                'features': ['mintable', 'burnable']
            },
            'spl': {
                'blockchain': 'Solana',
                'standard': 'SPL',
                'features': ['mintable', 'freeze']
            }
        }
    
    def generate_erc20(self, name, symbol, supply, decimals=18):
        """生成 ERC-20 代币合约"""
        contract = f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {symbol} is ERC20, ERC20Burnable, Ownable {{
    uint256 public constant TOTAL_SUPPLY = {supply} * 10**{decimals};
    
    mapping(address => bool) public minters;
    
    constructor() ERC20("{name}", "{symbol}") Ownable(msg.sender) {{
        _mint(msg.sender, TOTAL_SUPPLY);
    }}
    
    function mint(address to, uint256 amount) external onlyMinter {{
        _mint(to, amount);
    }}
    
    function addMinter(address account) external onlyOwner {{
        minters[account] = true;
    }}
    
    modifier onlyMinter() {{
        require(minters[msg.sender], "Not a minter");
        _;
    }}
}}'''
        return contract
    
    def generate_token(self, name, symbol, supply, chain='erc20'):
        """生成代币"""
        template = self.templates.get(chain, self.templates['erc20'])
        
        token_info = {
            'name': name,
            'symbol': symbol,
            'supply': supply,
            'chain': chain,
            'standard': template['standard'],
            'blockchain': template['blockchain'],
            'features': template['features'],
            'created_at': datetime.now().isoformat()
        }
        
        # 生成合约代码
        if chain == 'erc20' or chain == 'bep20':
            token_info['contract_code'] = self.generate_erc20(name, symbol, supply)
        
        return token_info
    
    def save_token(self, token_info):
        """保存代币配置"""
        os.makedirs('skills/xiami/defi/tokens', exist_ok=True)
        filename = f"skills/xiami/defi/tokens/{token_info['symbol']}_{token_info['chain']}.json"
        with open(filename, 'w') as f:
            json.dump(token_info, f, indent=2)
        return filename
    
    def list_tokens(self):
        """列出已生成的代币"""
        import glob
        tokens = []
        for f in glob.glob('skills/xiami/defi/tokens/*.json'):
            with open(f) as fp:
                tokens.append(json.load(fp))
        return tokens

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
XIAMI DeFi Token Creator

用法:
  python defi_token.py create <name> <symbol> <supply> [chain]
  python defi_token.py list
  python defi_token.py info <symbol>

示例:
  python defi_token.py create "MyToken" "MTK" 1000000
  python defi_token.py create "MyToken" "MTK" 1000000 bep20
""")
        return
    
    cmd = sys.argv[1]
    generator = TokenGenerator()
    
    if cmd == 'create':
        name = sys.argv[2]
        symbol = sys.argv[3]
        supply = int(sys.argv[4])
        chain = sys.argv[5] if len(sys.argv) > 5 else 'erc20'
        
        token = generator.generate_token(name, symbol, supply, chain)
        file_path = generator.save_token(token)
        
        print(f"✅ 代币生成成功!")
        print(f"   名称: {name}")
        print(f"   符号: {symbol}")
        print(f"   供应量: {supply}")
        print(f"   链: {token['blockchain']} ({chain})")
        print(f"   特性: {', '.join(token['features'])}")
        print(f"   配置: {file_path}")
    
    elif cmd == 'list':
        tokens = generator.list_tokens()
        print(f"\n📋 已生成的代币 ({len(tokens)}个)")
        for t in tokens:
            print(f"  - {t['name']} ({t['symbol']}) on {t['blockchain']}")
    
    elif cmd == 'info' and len(sys.argv) > 2:
        symbol = sys.argv[2]
        tokens = generator.list_tokens()
        for t in tokens:
            if t['symbol'] == symbol:
                print(f"\n🔍 {t['name']} ({t['symbol']})")
                print(f"   链: {t['blockchain']}")
                print(f"   标准: {t['standard']}")
                print(f"   供应量: {t['supply']}")
                print(f"   创建时间: {t['created_at']}")
                break
        else:
            print(f"代币 {symbol} 不存在")

if __name__ == '__main__':
    main()
