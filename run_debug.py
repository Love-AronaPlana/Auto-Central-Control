# 启动脚本（调试模式）

import asyncio
from start import main

if __name__ == "__main__":
    # 以调试模式启动
    asyncio.run(main(debug=True))