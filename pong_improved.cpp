/*
 * 文件名: pong_improved.cpp
 * 作业: 用函数编写Pong游戏并改进
 * 基础: 《现代C++编程实战》第4章 Pong游戏
 * 改进: D(暂停) + A(5分获胜) + C(底部提示栏)
 * 编译: g++ -std=c++14 -fexec-charset=UTF-8 pong_improved.cpp -o pong_improved.exe
 */

#include <iostream>
#include <random>
#include <thread>
#include <chrono>
#include <string>

#ifdef _WIN32
#include <windows.h>
#include <conio.h>

// 隐藏控制台光标
void hide_cursor() {
    HANDLE console = GetStdHandle(STD_OUTPUT_HANDLE);
    CONSOLE_CURSOR_INFO cursorInfo;
    GetConsoleCursorInfo(console, &cursorInfo);
    cursorInfo.bVisible = FALSE;
    SetConsoleCursorInfo(console, &cursorInfo);
}

// 显示控制台光标
void show_cursor() {
    HANDLE console = GetStdHandle(STD_OUTPUT_HANDLE);
    CONSOLE_CURSOR_INFO cursorInfo;
    GetConsoleCursorInfo(console, &cursorInfo);
    cursorInfo.bVisible = TRUE;
    SetConsoleCursorInfo(console, &cursorInfo);
}
#else
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>

int _kbhit() {
    struct termios oldt, newt;
    int ch, oldf;
    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
    oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);
    ch = getchar();
    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    fcntl(STDIN_FILENO, F_SETFL, oldf);
    if (ch != EOF) { ungetc(ch, stdin); return 1; }
    return 0;
}

char _getch() {
    struct termios oldt, newt;
    char ch;
    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
    ch = getchar();
    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    return ch;
}

void hide_cursor() { std::cout << "\033[?25l"; }
void show_cursor() { std::cout << "\033[?25h"; }
#endif

// 生成随机方向速度
#define RANDOM_DIRECTION(gen, velDist, dirDist) \
    (velDist(gen) * (dirDist(gen) ? 1 : -1))

// ========== 新增函数：绘制覆盖文字到帧缓冲 ==========

// 在帧缓冲中指定位置绘制一行文字
void draw_text_to_buffer(std::string& fb, int width, int row, int col, const std::string& text) {
    int idx = row * (width + 1) + col;
    for (size_t i = 0; i < text.size() && col + (int)i < width; i++) {
        fb[idx + i] = text[i];
    }
}

// 在帧缓冲中央绘制多行文字（用于暂停、游戏结束等覆盖层）
void draw_centered_overlay(std::string& fb, int width, int height,
                           const std::string& line1, const std::string& line2,
                           const std::string& line3, const std::string& line4) {
    int center_row = height / 2 - 2;
    int center_col = width / 2;

    if (!line1.empty()) draw_text_to_buffer(fb, width, center_row,
        center_col - (int)line1.size() / 2, line1);
    if (!line2.empty()) draw_text_to_buffer(fb, width, center_row + 1,
        center_col - (int)line2.size() / 2, line2);
    if (!line3.empty()) draw_text_to_buffer(fb, width, center_row + 2,
        center_col - (int)line3.size() / 2, line3);
    if (!line4.empty()) draw_text_to_buffer(fb, width, center_row + 3,
        center_col - (int)line4.size() / 2, line4);
}

// ========== 新增函数：绘制底部信息栏 ==========
void draw_info_bar(std::string& fb, int width, int height, bool paused, bool gameOver) {
    int row = height;
    // 绘制分隔线
    for (int x = 0; x < width; x++) fb[row * (width + 1) + x] = '-';
    fb[row * (width + 1) + width] = '\n';

    row = height + 1;
    std::string info;
    if (gameOver) {
        info = "  [R] 重新开始  |  [Q] 退出游戏";
    } else if (paused) {
        info = "  [P] 继续游戏  |  [Q] 退出游戏";
    } else {
        info = "  [W/S] 左挡板  |  [↑/↓] 右挡板  |  [P] 暂停  |  [Q] 退出  |  先得5分获胜！";
    }
    for (int x = 0; x < width; x++) {
        if (x < (int)info.size())
            fb[row * (width + 1) + x] = info[x];
        else
            fb[row * (width + 1) + x] = ' ';
    }
    fb[row * (width + 1) + width] = '\n';
}

// ========== 新增函数：重置游戏状态 ==========
void reset_game(int& score1, int& score2, int& ball_x, int& ball_y,
                int& ball_vec_x, int& ball_vec_y, int WIDTH, int HEIGHT,
                int& paddle1_y, int& paddle2_y, int paddle_h,
                std::mt19937& gen,
                std::uniform_int_distribution<int>& velDist,
                std::uniform_int_distribution<int>& dirDist,
                bool& paused, bool& gameOver, int& winner) {
    score1 = 0; score2 = 0;
    ball_x = WIDTH / 2; ball_y = HEIGHT / 2;
    ball_vec_x = RANDOM_DIRECTION(gen, velDist, dirDist);
    ball_vec_y = RANDOM_DIRECTION(gen, velDist, dirDist);
    paddle1_y = HEIGHT / 2 - paddle_h / 2;
    paddle2_y = HEIGHT / 2 - paddle_h / 2;
    paused = false;
    gameOver = false;
    winner = 0;
}

// ========== 新增函数：处理键盘输入 ==========
bool handle_input(int& paddle1_y, int& paddle2_y, int paddle_h, int HEIGHT,
                  int paddle1_vec, int paddle2_vec,
                  bool& paused, bool& gameOver,
                  int& score1, int& score2, int& ball_x, int& ball_y,
                  int& ball_vec_x, int& ball_vec_y, int WIDTH,
                  int paddle_h_val,
                  std::mt19937& gen,
                  std::uniform_int_distribution<int>& velDist,
                  std::uniform_int_distribution<int>& dirDist,
                  int& winner) {
    char key;
    if (!_kbhit()) return true;  // 无按键，继续运行

    key = _getch();

    // 暂停切换（游戏进行中才有效）
    if ((key == 'p' || key == 'P') && !gameOver) {
        paused = !paused;
        return true;
    }

    // 游戏结束后的操作
    if (gameOver) {
        if (key == 'r' || key == 'R') {
            reset_game(score1, score2, ball_x, ball_y, ball_vec_x, ball_vec_y,
                       WIDTH, HEIGHT, paddle1_y, paddle2_y, paddle_h_val,
                       gen, velDist, dirDist, paused, gameOver, winner);
        } else if (key == 'q' || key == 'Q') {
            return false;  // 退出游戏
        }
        return true;
    }

    // 暂停时只响应 P（上面已处理）和 Q
    if (paused) {
        if (key == 'q' || key == 'Q') {
            return false;
        }
        return true;
    }

    // 正常游戏操作
    if ((key == 'w' || key == 'W') && paddle1_y > paddle1_vec) {
        paddle1_y -= paddle1_vec;
    } else if ((key == 's' || key == 'S') && paddle1_y + paddle1_vec + paddle_h < HEIGHT) {
        paddle1_y += paddle1_vec;
    } else if (key == 72 && paddle2_y > paddle2_vec) {
        paddle2_y -= paddle2_vec;
    } else if (key == 80 && paddle2_y + paddle2_vec + paddle_h < HEIGHT) {
        paddle2_y += paddle2_vec;
    } else if (key == 'q' || key == 'Q') {
        return false;
    }

    return true;
}

// ========== 新增函数：更新游戏逻辑 ==========
void update_game(int& ball_x, int& ball_y, int& ball_vec_x, int& ball_vec_y,
                 int WIDTH, int HEIGHT,
                 int paddle_w, int paddle_h,
                 int /*paddle1_x*/, int paddle1_y,
                 int /*paddle2_x*/, int paddle2_y,
                 int& score1, int& score2,
                 bool& gameOver, int& winner,
                 std::mt19937& gen,
                 std::uniform_int_distribution<int>& velDist,
                 std::uniform_int_distribution<int>& dirDist) {
    ball_x += ball_vec_x;
    ball_y += ball_vec_y;

    // 碰上下墙反弹
    if (ball_y < 0 || ball_y >= HEIGHT) {
        ball_vec_y = -ball_vec_y;
    }

    // 碰左挡板反弹
    if (ball_x < paddle_w && ball_y >= paddle1_y && ball_y < paddle1_y + paddle_h) {
        ball_vec_x = -ball_vec_x;
        score1 += 1;
    }
    // 碰右挡板反弹
    else if (ball_x > WIDTH - paddle_w && ball_y >= paddle2_y && ball_y < paddle2_y + paddle_h) {
        ball_vec_x = -ball_vec_x;
        score2 += 1;
    }

    // 球出界，对方得分并重置球
    if (ball_x < 0 || ball_x > WIDTH) {
        if (ball_x < 0) score2++;
        else score1++;
        ball_x = WIDTH / 2;
        ball_y = HEIGHT / 2;
        ball_vec_x = RANDOM_DIRECTION(gen, velDist, dirDist);
        ball_vec_y = RANDOM_DIRECTION(gen, velDist, dirDist);
    }

    // 检查获胜条件：先得5分者获胜
    if (score1 >= 5) {
        gameOver = true;
        winner = 1;
    } else if (score2 >= 5) {
        gameOver = true;
        winner = 2;
    }
}

// ========== 新增函数：渲染画面 ==========
void render_frame(std::string& fb, int WIDTH, int HEIGHT, int /*INFO_H*/,
                  int ball_x, int ball_y,
                  int paddle1_x, int paddle1_y, int paddle2_x, int paddle2_y,
                  int paddle_w, int paddle_h,
                  int score1, int score2,
                  int score1_x, int score1_y, int score2_x, int score2_y,
                  bool paused, bool gameOver, int winner) {
    int frame_idx = 0;

    // 顶部墙
    for (int x = 0; x < WIDTH; x++) fb[frame_idx++] = '=';
    fb[frame_idx++] = '\n';

    // 游戏区域（跳过顶部和底部墙行）
    int game_area_bottom = HEIGHT;
    for (int y = 1; y < game_area_bottom; y++) {
        for (int x = 0; x < WIDTH; x++) {
            if (x == ball_x && y == ball_y)
                fb[frame_idx++] = 'O';  // 球
            else if (y >= paddle1_y && y < paddle1_y + paddle_h
                     && x >= paddle1_x && x < paddle1_x + paddle_w)
                fb[frame_idx++] = 'Z';  // 左挡板
            else if (y >= paddle2_y && y < paddle2_y + paddle_h
                     && x >= paddle2_x && x < paddle2_x + paddle_w)
                fb[frame_idx++] = 'Z';  // 右挡板
            else if (y == score1_y && x == score1_x) {
                fb[frame_idx++] = '0' + score1;  // 左侧分数（单数字 0-5）
                x += 0;  // 单字符，不需要额外跳过
            }
            else if (y == score2_y && x == score2_x) {
                fb[frame_idx++] = '0' + score2;  // 右侧分数
            }
            else if (x == 0 || x == WIDTH / 2 || x == WIDTH - 1)
                fb[frame_idx++] = '|';  // 边线和中线
            else
                fb[frame_idx++] = ' ';
        }
        fb[frame_idx++] = '\n';
    }

    // 底部墙
    for (int x = 0; x < WIDTH; x++) fb[frame_idx++] = '=';
    fb[frame_idx++] = '\n';

    // 覆盖层：暂停
    if (paused && !gameOver) {
        draw_centered_overlay(fb, WIDTH, HEIGHT,
            "╔══════════════════╗",
            "║    游 戏 暂 停   ║",
            "║  按 P 键继续...  ║",
            "╚══════════════════╝");
    }

    // 覆盖层：游戏结束
    if (gameOver) {
        std::string winner_text = "  PLAYER " + std::to_string(winner) + " 获胜！  ";
        draw_centered_overlay(fb, WIDTH, HEIGHT,
            "╔══════════════════════════╗",
            "║       游 戏 结 束        ║",
            "║  " + winner_text + "  ║",
            "╚══════════════════════════╝");
    }

    // 底部信息栏（在底部墙之外）
    draw_info_bar(fb, WIDTH, HEIGHT, paused, gameOver);
}

// ========== 主函数 ==========
int main() {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
#endif

    // 游戏参数
    const int WIDTH = 120;
    const int HEIGHT = 40;
    const int INFO_H = 2;  // 底部提示栏高度

    // 球
    int ball_x = WIDTH / 2, ball_y = HEIGHT / 2;
    int ball_vec_x = 0, ball_vec_y = 0;

    // 挡板
    const int paddle_w = 3, paddle_h = 10;
    const int paddle1_x = 0, paddle2_x = WIDTH - paddle_w;
    const int paddle1_vec = 3, paddle2_vec = 3;
    int paddle1_y = HEIGHT / 2 - paddle_h / 2;
    int paddle2_y = HEIGHT / 2 - paddle_h / 2;

    // 分数
    int score1 = 0, score2 = 0;
    const int score1_x = paddle_w + 8, score1_y = 2;
    const int score2_x = WIDTH - 8 - paddle_w, score2_y = 2;

    // 游戏状态（改进 D + A）
    bool paused = false;
    bool gameOver = false;
    int winner = 0;

    // 随机数
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> velDist(1, 3);
    std::uniform_int_distribution<int> dirDist(0, 1);

    ball_vec_x = RANDOM_DIRECTION(gen, velDist, dirDist);
    ball_vec_y = RANDOM_DIRECTION(gen, velDist, dirDist);

    // 帧缓冲（游戏区 HEIGHT 行 + 1 行底墙 + INFO_H 行信息栏）
    int total_rows = HEIGHT + 1 + INFO_H;
    std::string framebuffer(total_rows * (WIDTH + 1), ' ');

    hide_cursor();

    // 游戏主循环
    bool running = true;
    while (running) {

        // 1. 处理输入
        running = handle_input(paddle1_y, paddle2_y, paddle_h, HEIGHT,
                               paddle1_vec, paddle2_vec,
                               paused, gameOver,
                               score1, score2, ball_x, ball_y,
                               ball_vec_x, ball_vec_y, WIDTH,
                               paddle_h,
                               gen, velDist, dirDist, winner);

        // 2. 更新逻辑（暂停或结束时跳过物理更新）
        if (!paused && !gameOver) {
            update_game(ball_x, ball_y, ball_vec_x, ball_vec_y,
                        WIDTH, HEIGHT, paddle_w, paddle_h,
                        paddle1_x, paddle1_y, paddle2_x, paddle2_y,
                        score1, score2,
                        gameOver, winner, gen, velDist, dirDist);
        }

        // 3. 重置帧缓冲
        std::fill(framebuffer.begin(), framebuffer.end(), ' ');

        // 4. 渲染
        render_frame(framebuffer, WIDTH, HEIGHT, INFO_H,
                     ball_x, ball_y,
                     paddle1_x, paddle1_y, paddle2_x, paddle2_y,
                     paddle_w, paddle_h,
                     score1, score2,
                     score1_x, score1_y, score2_x, score2_y,
                     paused, gameOver, winner);

        // 5. 输出
#ifdef _WIN32
        SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), COORD{ 0, 0 });
        hide_cursor();
#else
        std::cout << "\033[H";
        hide_cursor();
#endif
        std::cout << framebuffer;

        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    // 游戏结束，显示光标并清屏
    show_cursor();
    std::cout << "\n\n感谢游玩 Pong 游戏！\n";
    return 0;
}
