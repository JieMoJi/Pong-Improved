#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pong游戏改进实验报告
依赖: pip install fpdf2
"""

import os, sys
from fpdf import FPDF

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

STUDENT_NAME   = "张轩基"
STUDENT_ID     = "1030425213"
STUDENT_CLASS  = "计科2502"
SUBMIT_DATE    = "2026.6.26"
GITHUB_URL     = "https://github.com/JieMoJi/Pong-Improved"
TITLE_CN       = "Pong游戏改进 — 用函数重构并增加暂停/获胜/提示栏"

def find_font():
    for p in ["C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf","C:/Windows/Fonts/simsun.ttc"]:
        if os.path.exists(p): return p
    raise RuntimeError("未找到中文字体")

FONT_PATH = find_font()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class PDF(FPDF):
    def __init__(self, fp):
        super().__init__('P','mm','A4')
        self.set_auto_page_break(True, 20)
        self.add_font('C','',fp)
        self.fn = 'C'
        self.fb = 11; self.fs = 9; self.fh2 = 15; self.fh3 = 12

    def footer(self):
        self.set_y(-15); self.set_font(self.fn,'',8)
        self.set_text_color(128,128,128)
        self.cell(0,10, f"{TITLE_CN} — 实验报告  |  第{self.page_no()}页", align='C')

    def body(self, t, s=None):
        if s is None: s = self.fb
        self.set_font(self.fn,'',s); self.multi_cell(0, s*0.62, t, align='L'); self.ln(2)

    def sec(self, title):
        self.ln(3); self.set_font(self.fn,'',self.fh2)
        self.set_text_color(0,51,102)
        self.cell(0,10,title,new_x="LMARGIN",new_y="NEXT")
        y=self.get_y(); self.set_draw_color(0,51,102); self.set_line_width(0.6)
        self.line(self.l_margin,y,self.w-self.r_margin,y); self.ln(5)
        self.set_text_color(0,0,0)

    def sub(self, title):
        self.set_font(self.fn,'',self.fh3); self.cell(0,8,title,new_x="LMARGIN",new_y="NEXT"); self.ln(3)

    def code(self, t, s=None):
        if s is None: s = self.fs
        self.set_font(self.fn,'',s); self.set_fill_color(245,245,245)
        self.set_draw_color(200,200,200); self.set_text_color(40,40,40)
        n = t.count('\n')+1; h = max(n*s*0.52, 8)
        if self.get_y()+h+6 > self.h-20: self.add_page()
        self.rect(self.get_x(),self.get_y(),self.w-self.l_margin-self.r_margin, h+5, style='DF')
        self.set_xy(self.get_x()+2,self.get_y()+3)
        self.multi_cell(self.w-self.l_margin-self.r_margin-4, s*0.52, t)
        self.set_text_color(0,0,0); self.ln(3)

    def cover(self):
        self.add_page(); self.ln(20)
        self.set_font(self.fn,'',26); self.set_text_color(0,51,102)
        self.cell(0,16,"Pong 游戏改进",align='C',new_x="LMARGIN",new_y="NEXT")
        self.set_font(self.fn,'',14); self.set_text_color(80,80,80)
        self.cell(0,10,"用函数重构 + 暂停/获胜/提示栏",align='C',new_x="LMARGIN",new_y="NEXT"); self.ln(8)
        self.set_draw_color(0,51,102); self.set_line_width(0.8)
        cx=self.w/2-45; self.line(cx,self.get_y(),cx+90,self.get_y()); self.ln(14)
        self.set_font(self.fn,'',13); self.set_text_color(0,0,0)
        for l,v in [("姓    名：",STUDENT_NAME),("学    号：",STUDENT_ID),
                     ("班    级：",STUDENT_CLASS),("提交日期：",SUBMIT_DATE),
                     ("源代码  ：",GITHUB_URL)]:
            self.cell(0,10,l+v,align='C',new_x="LMARGIN",new_y="NEXT"); self.ln(2)
        self.ln(18)
        self.set_font(self.fn,'',9); self.set_text_color(150,150,150)
        self.cell(0,8,"改进 D (暂停) + A (5分获胜) + C (底部提示栏)",align='C',new_x="LMARGIN",new_y="NEXT")
        self.set_text_color(0,0,0)


# ============================================================
# 报告内容
# ============================================================

S1_FLOW = (
    "原版 Pong 游戏的主流程遵循经典的「游戏循环」模式：\n\n"
    "┌─────────────────────────────────────────┐\n"
    "│  1. 初始化                                │\n"
    "│     · 设置窗口大小 (120×40)              │\n"
    "│     · 初始化球的位置和随机速度            │\n"
    "│     · 初始化左右挡板位置和移动速度        │\n"
    "│     · 初始化分数为 0                      │\n"
    "│     · 分配帧缓冲区 (framebuffer)          │\n"
    "│     · 隐藏光标                            │\n"
    "├─────────────────────────────────────────┤\n"
    "│  2. while(true) 游戏主循环                │\n"
    "│     ┌───────────────────────────────┐    │\n"
    "│     │ 2a. 输入处理                   │    │\n"
    "│     │   _kbhit() 检测 → _getch() 读取│    │\n"
    "│     │   if-else 分支: W/S/↑/↓/Q     │    │\n"
    "│     ├───────────────────────────────┤    │\n"
    "│     │ 2b. 更新逻辑                   │    │\n"
    "│     │   球移动 → 碰撞检测 → 计分     │    │\n"
    "│     │   碰墙反弹 / 碰挡板反弹+计分   │    │\n"
    "│     │   出界 → 对方得分 + 球重置     │    │\n"
    "│     ├───────────────────────────────┤    │\n"
    "│     │ 2c. 渲染画面                   │    │\n"
    "│     │   光标复位 (0,0)               │    │\n"
    "│     │   嵌套 for 填充帧缓冲          │    │\n"
    "│     │   输出 framebuffer              │    │\n"
    "│     ├───────────────────────────────┤    │\n"
    "│     │ 2d. sleep(50ms) 控制帧率       │    │\n"
    "│     └───────────────────────────────┘    │\n"
    "│     循环直到 Q 键触发 break               │\n"
    "├─────────────────────────────────────────┤\n"
    "│  3. 清理                                  │\n"
    "│     · 显示光标                            │\n"
    "│     · return 0                            │\n"
    "└─────────────────────────────────────────┘"
)

S2_CHOICE = (
    "本次实验选择了以下三项改进，以 D（暂停功能）为主，A（5分获胜条件）和 C（底部提示栏）为辅：\n\n"
    "【改进 D — 暂停功能】（主要改进）\n"
    "按下 P 键可暂停/继续游戏。暂停时：\n"
    "· 球的物理更新停止（跳过 update_game 函数调用）\n"
    "· 挡板移动禁用（跳过正常操作的按键处理）\n"
    "· 画面中央显示「游戏暂停」覆盖层\n"
    "· 底部提示栏切换为暂停模式的操作说明\n\n"
    "【改进 A — 获胜条件】\n"
    "先得 5 分者获胜。新增以下逻辑：\n"
    "· 每次计分后检查 score1 >= 5 或 score2 >= 5\n"
    "· 满足条件时设置 gameOver=true，winner=1或2\n"
    "· 画面中央显示获胜信息覆盖层\n"
    "· 底部提示栏切换为「按 R 重新开始 / 按 Q 退出」\n\n"
    "【改进 C — 底部提示栏】\n"
    "在游戏画面底部增加了 2 行信息栏：\n"
    "· 正常模式：显示 W/S（左挡板）、↑/↓（右挡板）、P（暂停）、Q（退出）以及获胜条件\n"
    "· 暂停模式：显示 P（继续）、Q（退出）\n"
    "· 结束模式：显示 R（重新开始）、Q（退出）\n"
    "· 提示栏与游戏画面之间用分隔线隔开，视觉清晰"
)

S3_FUNCTIONS = (
    "本次改进的关键变化是：将原版全部写在 main() 中的代码拆分为 6 个独立函数，\n"
    "每个函数负责单一职责。以下是所有新增/修改的函数说明：\n\n"
    "1. handle_input() — 输入处理函数\n"
    "   职责：统一处理所有键盘输入，根据游戏状态（正常/暂停/结束）决定响应方式。\n"
    "   参数：挡板位置引用、暂停状态引用、游戏结束状态引用、分数引用等\n"
    "   返回：bool（true=继续运行，false=退出程序）\n"
    "   新增逻辑：P键暂停切换、R键重新开始（仅gameOver时有效）、暂停/结束时禁用挡板操作\n\n"
    "2. update_game() — 游戏逻辑更新函数\n"
    "   职责：更新球的位置、处理碰撞检测、计分、检测获胜条件。\n"
    "   参数：球的位置和速度引用、分数引用、gameOver和winner引用\n"
    "   新增逻辑：计分后检查 score>=5 → 设置 gameOver=true\n\n"
    "3. render_frame() — 画面渲染函数\n"
    "   职责：填充帧缓冲（墙壁、球、挡板、分数），绘制覆盖层和底部信息栏。\n"
    "   新增逻辑：根据 paused/gameOver 状态绘制不同的覆盖层文字\n\n"
    "4. draw_text_to_buffer() — 辅助函数：在帧缓冲指定位置写文字\n"
    "   职责：向帧缓冲指定坐标写入一段文字，用于覆盖层显示。\n\n"
    "5. draw_centered_overlay() — 辅助函数：居中覆盖层\n"
    "   职责：在画面中央绘制多行文字框（用于暂停和游戏结束的提示）。\n"
    "   参数：帧缓冲引用、画面宽高、4行文字内容（空字符串表示跳过该行）\n\n"
    "6. draw_info_bar() — 辅助函数：底部信息栏\n"
    "   职责：根据游戏状态（正常/暂停/结束）在画面底部绘制不同的操作提示。\n"
    "   参数：帧缓冲引用、画面宽高、paused和gameOver状态\n\n"
    "7. reset_game() — 辅助函数：重置游戏状态\n"
    "   职责：将所有游戏变量恢复为初始值（分数归零、球重置、挡板归位、状态重置）。\n"
    "   参数：所有游戏状态变量的引用\n\n"
    "函数调用关系：\n"
    "  main()\n"
    "    ├── handle_input()          每一帧调用，处理按键\n"
    "    ├── update_game()           仅当 !paused && !gameOver 时调用\n"
    "    ├── render_frame()          每一帧调用\n"
    "    │     ├── draw_centered_overlay()  绘制暂停/获胜覆盖层\n"
    "    │     └── draw_info_bar()          绘制底部提示栏\n"
    "    └── reset_game()            按 R 重新开始时调用"
)

# 关键代码片段
CODE_INPUT = """// handle_input() 中的暂停逻辑（改进 D 核心）
bool handle_input(..., bool& paused, bool& gameOver, ...) {
    char key;
    if (!_kbhit()) return true;   // 无按键，继续运行

    key = _getch();

    // 暂停切换（游戏进行中才有效）
    if ((key == 'p' || key == 'P') && !gameOver) {
        paused = !paused;
        return true;
    }

    // 游戏结束后的 R 重新开始（改进 A）
    if (gameOver) {
        if (key == 'r' || key == 'R') {
            reset_game(...);       // 重置所有状态
        } else if (key == 'q' || key == 'Q') {
            return false;          // 退出
        }
        return true;
    }

    // 暂停时只响应已处理的 P 和下面的 Q
    if (paused) {
        if (key == 'q' || key == 'Q') return false;
        return true;              // 忽略挡板操作
    }

    // 正常操作：W/S 左挡板，方向键右挡板，Q 退出
    if ((key == 'w' || key == 'W') && paddle1_y > paddle1_vec) { ... }
    ...
}"""

CODE_UPDATE = """// update_game() 中的获胜检测（改进 A 核心）
void update_game(..., int& score1, int& score2,
                 bool& gameOver, int& winner, ...) {
    ...  // 球移动 + 碰撞检测 + 出界计分（与原版相同）

    // 检查获胜条件：先得 5 分者获胜
    if (score1 >= 5) {
        gameOver = true;
        winner = 1;
    } else if (score2 >= 5) {
        gameOver = true;
        winner = 2;
    }
}"""

CODE_RENDER = """// render_frame() 中的覆盖层绘制（改进 D + A）
void render_frame(..., bool paused, bool gameOver, int winner) {
    ...  // 绘制墙壁、球、挡板、分数

    // 暂停覆盖层
    if (paused && !gameOver) {
        draw_centered_overlay(fb, WIDTH, HEIGHT,
            "╔══════════════════╗",
            "║    游 戏 暂 停   ║",
            "║  按 P 键继续...  ║",
            "╚══════════════════╝");
    }

    // 游戏结束覆盖层
    if (gameOver) {
        string winner_text =
            "  PLAYER " + to_string(winner) + " 获胜！  ";
        draw_centered_overlay(fb, WIDTH, HEIGHT,
            "╔══════════════════════════╗",
            "║       游 戏 结 束        ║",
            "║  " + winner_text + "  ║",
            "╚══════════════════════════╝");
    }

    // 底部信息栏（改进 C）
    draw_info_bar(fb, WIDTH, HEIGHT, paused, gameOver);
}"""

CODE_INFO_BAR = """// draw_info_bar() 根据状态切换提示文字（改进 C 核心）
void draw_info_bar(string& fb, int WIDTH, int HEIGHT,
                   bool paused, bool gameOver) {
    string info;
    if (gameOver) {
        info = "  [R] 重新开始  |  [Q] 退出游戏";
    } else if (paused) {
        info = "  [P] 继续游戏  |  [Q] 退出游戏";
    } else {
        info = "  [W/S] 左挡板  |  [↑/↓] 右挡板  |"
               "  [P] 暂停  |  [Q] 退出  |  先得5分获胜！";
    }
    // 将 info 写入帧缓冲最后一行
    int row = HEIGHT + 1;
    for (int x = 0; x < (int)info.size() && x < WIDTH; x++)
        fb[row * (WIDTH + 1) + x] = info[x];
    ...
}"""

CODE_MAIN = """// main() 中的游戏主循环（改进后的简化结构）
int main() {
    ...  // 变量声明 + 初始化

    bool paused = false;      // 新增：暂停状态
    bool gameOver = false;    // 新增：游戏结束状态
    int winner = 0;           // 新增：获胜者编号

    bool running = true;
    while (running) {
        // 1. 处理输入（含暂停/重新开始逻辑）
        running = handle_input(...);

        // 2. 更新逻辑（暂停或结束时跳过）
        if (!paused && !gameOver) {
            update_game(...);
        }

        // 3. 渲染画面（含覆盖层和信息栏）
        render_frame(...);

        // 4. 输出 + 延时
        cout << framebuffer;
        sleep_for(50ms);
    }
}"""

S4_PROBLEMS = (
    "问题 1：暂停时挡板仍能移动\n"
    "现象：暂停后按 W/S/↑/↓ 键，挡板竟然还在动。\n"
    "原因：原版的按键处理逻辑在 handle_input() 中先读取了按键，\n"
    "      暂停标记的设置和挡板操作在同一个函数的不同分支中，\n"
    "      但挡板移动的判断条件写在了暂停判断之前。\n"
    "解决：调整 if-else if 的顺序——先判断暂停状态，暂停时跳过所有挡板操作。\n"
    "      重构后的 handle_input() 按照 「P键 → 游戏结束操作 → 暂停阻挡 → 正常操作」\n"
    "      的顺序组织分支，确保了暂停时所有游戏操作都被拦截。\n\n"
    "问题 2：游戏结束后球仍在移动\n"
    "现象：获胜弹窗显示了，但画面上的球还在飞，分数还在变化。\n"
    "原因：原来的更新逻辑放在主循环中无条件执行，没有检查 gameOver 状态。\n"
    "解决：在调用 update_game() 前增加条件判断：if (!paused && !gameOver)。\n"
    "      游戏结束或暂停时，物理更新被完全跳过，画面冻结在结束瞬间。\n\n"
    "问题 3：重新开始后状态残留\n"
    "现象：按 R 重新开始后，旧的「游戏结束」文字仍然显示在画面上。\n"
    "原因：重置时只重置了分数和球的位置，没有把 gameOver 和 winner 重置。\n"
    "解决：编写专门的 reset_game() 函数，一次性重置所有 10+ 个状态变量，\n"
    "      避免遗漏。函数将 paused、gameOver、winner 以及所有游戏数据统一归零。\n\n"
    "问题 4：帧缓冲大小不足\n"
    "现象：添加底部信息栏后，文字显示不完整或覆盖了底部墙。\n"
    "原因：原版帧缓冲大小为 HEIGHT*(WIDTH+1)，刚好容纳游戏画面。\n"
    "      新增的信息栏需要额外的行。\n"
    "解决：扩展帧缓冲大小为 (HEIGHT+1+INFO_H)*(WIDTH+1)，其中 INFO_H=2，\n"
    "      多出 2 行用于底部提示栏。同时修改渲染函数，将信息栏写在这两行中。"
)

S5_SUMMARY = (
    "通过本次实验，我完成了从「阅读代码 → 理解流程 → 函数拆分 → 功能扩展」的完整过程，\n"
    "主要收获如下：\n\n"
    "1. 函数拆分提升了代码的可维护性：\n"
    "原版 Pong 的全部逻辑（初始化、输入、更新、渲染）都写在 main() 中，约 140 行。\n"
    "改进后拆分为 7 个函数，main() 缩减到约 50 行，变成一个清晰的「初始化→循环→清理」骨架。\n"
    "每个函数的职责单一明确，单独修改某项功能不再需要翻阅整个 main()。\n\n"
    "2. 状态管理是游戏编程的核心：\n"
    "引入 paused 和 gameOver 两个布尔变量后，游戏从「单状态（运行中）」变为「三状态\n"
    "（运行中/暂停/结束）」。状态变量的引入使得：\n"
    "· 输入处理需要根据状态决定响应哪些按键\n"
    "· 更新逻辑需要根据状态决定是否执行\n"
    "· 渲染需要根据状态决定显示什么覆盖层\n"
    "这种「状态驱动」的设计模式是游戏编程的基本范式。\n\n"
    "3. 帧缓冲技术理解加深：\n"
    "通过向帧缓冲写入覆盖层文字（而非简单的 cout），理解了为什么游戏使用帧缓冲\n"
    "而非逐行输出：它允许在渲染的最后阶段叠加 UI 元素（暂停提示、信息栏），\n"
    "而不会与游戏画面产生闪烁或错位。\n\n"
    "4. 改进选择的心得：\n"
    "选择 D+A+C 三项组合而非单独一项，因为这三项之间有自然的配合关系：\n"
    "· 暂停（D）需要底部提示栏（C）来告知玩家当前状态和操作方式\n"
    "· 获胜条件（A）使游戏有了「结束状态」，暂停（D）需要区分「运行中暂停」和「结束后暂停」\n"
    "· 信息栏（C）在三种状态下显示不同内容，与 A 和 D 共同构成完整的状态反馈系统\n"
    "三项改进协同形成了一个有头有尾、操作清晰的完整游戏体验。"
)


# ============================================================
# 主流程
# ============================================================
def main():
    print(f"使用字体: {FONT_PATH}")
    pdf = PDF(FONT_PATH)

    # ==== 封面 ====
    pdf.cover()

    # ==== 1. 游戏流程分析 ====
    pdf.add_page()
    pdf.sec("1. 原版 Pong 游戏流程分析")
    pdf.body(S1_FLOW)

    # ==== 2. 改进任务说明 ====
    pdf.add_page()
    pdf.sec("2. 改进任务选择与说明")
    pdf.body(S2_CHOICE)

    # ==== 3. 函数设计与改动说明 ====
    pdf.sec("3. 函数设计与代码改动")
    pdf.body(S3_FUNCTIONS)

    pdf.sub("3.1 核心改动代码 — 输入处理（暂停逻辑）")
    pdf.code(CODE_INPUT)

    pdf.sub("3.2 核心改动代码 — 获胜检测")
    pdf.code(CODE_UPDATE)

    pdf.sub("3.3 核心改动代码 — 覆盖层与信息栏渲染")
    pdf.code(CODE_RENDER)

    pdf.sub("3.4 核心改动代码 — 底部信息栏")
    pdf.code(CODE_INFO_BAR)

    pdf.sub("3.5 主循环改动")
    pdf.code(CODE_MAIN)

    # ==== 4. 问题与解决方案 ====
    pdf.add_page()
    pdf.sec("4. 遇到的问题与解决方法")
    pdf.body(S4_PROBLEMS)

    # ==== 5. 总结 ====
    pdf.sec("5. 实验总结与心得")
    pdf.body(S5_SUMMARY)

    # ==== 对比表格 ====
    pdf.sub("原版 vs 改进版 对比")
    pdf.ln(2)
    col_w = [50, 70, 70]
    headers = ["维度", "原版 Pong", "改进版 Pong"]
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(pdf.fn, '', 9)
    y_top = pdf.get_y()
    for i, h in enumerate(headers):
        pdf.set_xy(pdf.l_margin + sum(col_w[:i]), y_top)
        pdf.cell(col_w[i], 9, " " + h, border=1, fill=True)
    pdf.set_xy(pdf.l_margin, y_top + 9)

    compare_data = [
        ("代码结构", "全部在 main() 中，约 140 行", "7 个函数，main() 约 50 行"),
        ("函数数量", "main() + 2 个平台函数", "main() + 2 平台函数 + 7 个业务函数"),
        ("游戏状态", "单状态（运行中）", "三状态（运行/暂停/结束）"),
        ("暂停功能", "无", "P 键切换，画面冻结 + 覆盖层"),
        ("获胜条件", "无（无限循环）", "先得 5 分获胜，显示获胜者"),
        ("重新开始", "无（只能退出重进）", "R 键一键重置所有状态"),
        ("操作提示", "无", "底部 2 行动态提示栏，随状态切换"),
        ("输入处理", "if-else 分支", "函数化，按游戏状态分层响应"),
    ]
    for j, row in enumerate(compare_data):
        pdf.set_fill_color(245, 248, 252) if j % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(pdf.fn, '', 8)
        max_lines = 1
        for i, cell_text in enumerate(row):
            n = cell_text.count('\n') + 1
            if n > max_lines: max_lines = n
        row_h = max(8, max_lines * 6)
        if pdf.get_y() + row_h > pdf.h - 25:
            pdf.add_page()
        for i, cell_text in enumerate(row):
            x_cell = pdf.l_margin + sum(col_w[:i])
            pdf.set_xy(x_cell, pdf.get_y())
            pdf.cell(col_w[i], row_h, " " + cell_text, border=1, fill=True)
        pdf.ln(row_h)
    pdf.ln(8)

    # ==== 输出 ====
    fname = f"{STUDENT_ID}_{STUDENT_NAME}_Pong改进实验报告_v2.pdf"
    out = os.path.join(BASE_DIR, fname)
    pdf.output(out)
    kb = os.path.getsize(out)/1024
    print(f"报告已生成: {out}")
    print(f"文件大小: {kb:.1f} KB  |  页数: {pdf.pages_count} 页")

if __name__ == "__main__":
    main()
