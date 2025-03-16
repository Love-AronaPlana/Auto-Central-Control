# 启动脚本（正常模式）

import asyncio
from start import main

if __name__ == "__main__":
    # 以正常模式启动
    asyncio.run(main(debug=False))