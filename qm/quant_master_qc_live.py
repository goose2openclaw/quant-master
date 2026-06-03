"""QuantMaster Q@C 实盘版本"""
import sys
sys.path.insert(0, '/home/goose/.openclaw/workspace/quant_master')

from qm.quant_master_qc4 import QuantMasterQC4

if __name__ == '__main__':
    qm = QuantMasterQC4(10000)
    qm.mode = 'LIVE'
    qm.run()
