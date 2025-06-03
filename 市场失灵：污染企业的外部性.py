import pygame
import sys
import math
import numpy as np
from pygame.locals import *

# 初始化pygame
pygame.init()

# 屏幕设置 - 更大的尺寸
WIDTH, HEIGHT = 1400, 900  # 扩大屏幕尺寸
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("市场失灵：外部性挑战")

# 颜色定义 - 调整为白色背景
BACKGROUND = (255, 255, 255)  # 白色背景
PANEL_COLOR = (230, 240, 250)  # 浅蓝色面板
ACCENT_COLOR = (70, 130, 180)  # 深蓝色强调色
HIGHLIGHT_COLOR = (100, 200, 255)  # 亮蓝色高亮
TEXT_COLOR = (40, 50, 70)  # 深蓝色文字
WARNING_COLOR = (220, 60, 60)  # 红色警告
POSITIVE_COLOR = (60, 180, 80)  # 绿色正面
NEUTRAL_COLOR = (150, 150, 170)  # 灰色中性

# 字体
title_font = pygame.font.SysFont("simhei", 48, bold=True)  # 加大字体
header_font = pygame.font.SysFont("simhei", 36)
normal_font = pygame.font.SysFont("simhei", 30)
small_font = pygame.font.SysFont("simhei", 24)


# 游戏参数
class GameState:
    def __init__(self):
        self.round = 1
        self.total_rounds = 5
        self.production = 0
        self.profit = 0
        self.cumulative_pollution = 0
        self.social_cost = 0
        self.round_history = []
        self.total_profit = 0
        self.total_social_cost = 0
        self.social_welfare = 0

        # 最优值计算
        self.optimal_production = 60

    def calculate_effects(self):
        # 计算利润（简单线性关系）
        self.profit = self.production * 2

        # 计算污染（非线性关系）
        pollution = self.production * (1 + self.production / 100)
        self.cumulative_pollution += pollution

        # 计算社会成本（随着污染累积而增加）
        self.social_cost = self.cumulative_pollution * 1.2

        # 记录本轮历史
        self.round_history.append({
            "round": self.round,
            "production": self.production,
            "profit": self.profit,
            "pollution": pollution,
            "social_cost": self.social_cost
        })

        # 更新总统计
        self.total_profit += self.profit
        self.total_social_cost += self.social_cost
        self.social_welfare = self.total_profit - self.total_social_cost

        # 进入下一轮
        self.round += 1
        self.production = 0

    def get_round_data(self, round_num):
        for data in self.round_history:
            if data["round"] == round_num:
                return data
        return None


# 按钮类
class Button:
    def __init__(self, x, y, width, height, text, color=ACCENT_COLOR, hover_color=HIGHLIGHT_COLOR):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, TEXT_COLOR, self.rect, 2, border_radius=10)

        text_surf = normal_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


# 创建游戏状态
game = GameState()

# 创建按钮 - 位置调整以适应更大屏幕
submit_button = Button(WIDTH // 2 - 120, 750, 240, 70, "提交决策")
reset_button = Button(WIDTH // 2 - 120, 750, 240, 70, "重新开始")


# 绘制圆环进度图
def draw_round_progress(surface, x, y, radius, current_round, total_rounds):
    # 绘制背景圆
    pygame.draw.circle(surface, PANEL_COLOR, (x, y), radius)

    # 绘制进度
    angle_per_round = 360 / total_rounds
    start_angle = -90
    for i in range(total_rounds):
        end_angle = start_angle + angle_per_round
        color = HIGHLIGHT_COLOR if i < current_round - 1 else NEUTRAL_COLOR
        pygame.draw.arc(surface, color, (x - radius, y - radius, radius * 2, radius * 2),
                        math.radians(start_angle), math.radians(end_angle), 15)
        start_angle = end_angle

    # 绘制当前回合文本
    round_text = header_font.render(f"回合 {min(current_round, total_rounds)}/{total_rounds}", True, TEXT_COLOR)
    round_rect = round_text.get_rect(center=(x, y - 10))
    surface.blit(round_text, round_rect)

    status = "进行中" if current_round <= total_rounds else "已完成"
    status_text = small_font.render(f"状态: {status}", True, NEUTRAL_COLOR)
    status_rect = status_text.get_rect(center=(x, y + 20))
    surface.blit(status_text, status_rect)


# 绘制生产滑块
def draw_production_slider(surface, x, y, width, production):
    # 绘制滑块背景
    slider_rect = pygame.Rect(x, y, width, 50)  # 增加高度
    pygame.draw.rect(surface, PANEL_COLOR, slider_rect, border_radius=20)

    # 绘制滑块位置
    handle_x = x + (production / 100) * width
    pygame.draw.circle(surface, HIGHLIGHT_COLOR, (int(handle_x), y + 25), 30)  # 加大滑块

    # 绘制标记
    pygame.draw.line(surface, TEXT_COLOR, (x, y + 60), (x, y + 70), 3)
    pygame.draw.line(surface, TEXT_COLOR, (x + width // 2, y + 60), (x + width // 2, y + 70), 3)
    pygame.draw.line(surface, TEXT_COLOR, (x + width, y + 60), (x + width, y + 70), 3)

    # 绘制文本
    min_text = small_font.render("0", True, TEXT_COLOR)
    min_rect = min_text.get_rect(midtop=(x, y + 70))
    surface.blit(min_text, min_rect)

    mid_text = small_font.render("50", True, TEXT_COLOR)
    mid_rect = mid_text.get_rect(midtop=(x + width // 2, y + 70))
    surface.blit(mid_text, mid_rect)

    max_text = small_font.render("100", True, TEXT_COLOR)
    max_rect = max_text.get_rect(midtop=(x + width, y + 70))
    surface.blit(max_text, max_rect)

    # 绘制当前值
    value_text = header_font.render(f"{production} 单位", True, HIGHLIGHT_COLOR)
    value_rect = value_text.get_rect(midbottom=(x + width // 2, y - 20))
    surface.blit(value_text, value_rect)

    return slider_rect


# 绘制经济指标卡片
def draw_metric_card(surface, x, y, width, height, title, value, color, unit=""):
    # 绘制卡片
    pygame.draw.rect(surface, PANEL_COLOR, (x, y, width, height), border_radius=15)
    pygame.draw.rect(surface, color, (x, y, width, 60), border_radius=15)  # 增加标题栏高度

    # 绘制标题
    title_surf = normal_font.render(title, True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(x + width // 2, y + 30))
    surface.blit(title_surf, title_rect)

    # 绘制值
    value_surf = header_font.render(f"{value}{unit}", True, TEXT_COLOR)
    value_rect = value_surf.get_rect(center=(x + width // 2, y + height // 2 + 20))
    surface.blit(value_surf, value_rect)

    # 绘制描述
    if title == "个人利润":
        desc = "企业获得的直接收益"
    elif title == "社会成本":
        desc = "污染造成的环境损失"
    else:
        desc = "社会整体福利水平"

    desc_surf = small_font.render(desc, True, NEUTRAL_COLOR)
    desc_rect = desc_surf.get_rect(center=(x + width // 2, y + height - 30))
    surface.blit(desc_surf, desc_rect)


# 绘制历史图表
def draw_history_chart(surface, x, y, width, height, history):
    # 绘制背景
    pygame.draw.rect(surface, PANEL_COLOR, (x, y, width, height), border_radius=15)

    # 绘制标题
    title = "历史决策分析"
    title_surf = header_font.render(title, True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(x + width // 2, y + 50))  # 下移标题
    surface.blit(title_surf, title_rect)

    if len(history) == 0:
        no_data = small_font.render("暂无历史数据", True, NEUTRAL_COLOR)
        no_data_rect = no_data.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(no_data, no_data_rect)
        return

    # 计算最大值和比例
    max_production = max([data["production"] for data in history] + [100])
    max_cost = max([data["social_cost"] for data in history] + [100])

    # 绘制坐标轴
    pygame.draw.line(surface, TEXT_COLOR, (x + 80, y + height - 100), (x + width - 80, y + height - 100), 3)
    pygame.draw.line(surface, TEXT_COLOR, (x + 80, y + height - 100), (x + 80, y + 120), 3)

    # 绘制图例
    pygame.draw.line(surface, HIGHLIGHT_COLOR, (x + width - 200, y + 140), (x + width - 150, y + 140), 4)
    prod_legend = small_font.render("生产量", True, HIGHLIGHT_COLOR)
    surface.blit(prod_legend, (x + width - 140, y + 135))

    pygame.draw.line(surface, WARNING_COLOR, (x + width - 200, y + 180), (x + width - 150, y + 180), 4)
    cost_legend = small_font.render("社会成本", True, WARNING_COLOR)
    surface.blit(cost_legend, (x + width - 140, y + 175))

    # 绘制数据点
    point_radius = 10
    for i, data in enumerate(history):
        x_pos = x + 80 + (i + 1) * (width - 160) / (game.total_rounds + 1)

        # 绘制生产量点
        y_prod = y + height - 100 - (data["production"] / max_production) * (height - 220)
        pygame.draw.circle(surface, HIGHLIGHT_COLOR, (int(x_pos), int(y_prod)), point_radius)

        # 绘制社会成本点
        y_cost = y + height - 100 - (data["social_cost"] / max_cost) * (height - 220)
        pygame.draw.circle(surface, WARNING_COLOR, (int(x_pos), int(y_cost)), point_radius)

        # 绘制连接线（生产量）
        if i > 0:
            prev_x = x + 80 + (i) * (width - 160) / (game.total_rounds + 1)
            prev_y_prod = y + height - 100 - (history[i - 1]["production"] / max_production) * (height - 220)
            pygame.draw.line(surface, HIGHLIGHT_COLOR, (prev_x, prev_y_prod), (x_pos, y_prod), 3)

            prev_y_cost = y + height - 100 - (history[i - 1]["social_cost"] / max_cost) * (height - 220)
            pygame.draw.line(surface, WARNING_COLOR, (prev_x, prev_y_cost), (x_pos, y_cost), 3)

        # 绘制回合标签
        round_text = small_font.render(f"回合 {data['round']}", True, TEXT_COLOR)
        round_rect = round_text.get_rect(center=(int(x_pos), y + height - 70))  # 下移标签
        surface.blit(round_text, round_rect)


# 绘制历史数据表格 - 修改后的版本
def draw_history_table(surface, x, y, width, height, history):
    # 绘制背景
    pygame.draw.rect(surface, PANEL_COLOR, (x, y, width, height), border_radius=15)

    # 绘制标题
    title = "详细历史数据"
    title_surf = header_font.render(title, True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(x + width // 2, y + 30))  # 上移标题
    surface.blit(title_surf, title_rect)

    if len(history) == 0:
        no_data = small_font.render("暂无历史数据", True, NEUTRAL_COLOR)
        no_data_rect = no_data.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(no_data, no_data_rect)
        return

    # 绘制表头
    headers = ["回合", "生产量", "利润", "污染", "社会成本"]
    col_width = width // len(headers)

    for i, header in enumerate(headers):
        header_surf = small_font.render(header, True, ACCENT_COLOR)  # 使用较小字体
        header_rect = header_surf.get_rect(center=(x + i * col_width + col_width // 2, y + 70))  # 上移表头
        surface.blit(header_surf, header_rect)

    # 减小行高（从60减小到40）
    row_height = 40

    # 绘制数据行
    for row_idx, data in enumerate(history):
        row_y = y + 100 + row_idx * row_height  # 减小行高和起始位置

        # 绘制背景行
        row_color = (220, 230, 245) if row_idx % 2 == 0 else (210, 225, 245)
        pygame.draw.rect(surface, row_color, (x + 20, row_y - 15, width - 40, row_height), border_radius=8)

        # 绘制数据（使用较小字体）
        values = [
            str(data["round"]),
            f"{data['production']} 单位",
            f"￥{data['profit']}",
            f"{int(data['pollution'])}",
            f"￥{int(data['social_cost'])}"
        ]

        for i, value in enumerate(values):
            value_surf = small_font.render(value, True, TEXT_COLOR)  # 使用较小字体
            value_rect = value_surf.get_rect(
                center=(x + i * col_width + col_width // 2, row_y + row_height // 2 - 5))  # 微调垂直位置
            surface.blit(value_surf, value_rect)

    # 绘制总计栏（移到表格最底部）
    total_y = y + height - 50  # 总计栏位置下移

    # 绘制总计栏背景
    pygame.draw.rect(surface, (200, 220, 240), (x + 20, total_y, width - 40, 40), border_radius=8)

    # 绘制总计文本
    total_text = small_font.render("总计", True, ACCENT_COLOR)  # 使用较小字体
    total_rect = total_text.get_rect(center=(x + col_width // 2, total_y + 20))
    surface.blit(total_text, total_rect)

    # 计算总计值
    total_prod = sum([d["production"] for d in history])
    total_profit = sum([d["profit"] for d in history])
    total_pollution = sum([d["pollution"] for d in history])
    total_social_cost = sum([d["social_cost"] for d in history])

    totals = [
        f"{total_prod} 单位",
        f"￥{total_profit}",
        f"{int(total_pollution)}",
        f"￥{int(total_social_cost)}"
    ]

    # 绘制总计值（使用较小字体）
    for i, total in enumerate(totals):
        total_surf = small_font.render(total, True, TEXT_COLOR)  # 使用较小字体
        total_rect = total_surf.get_rect(center=(x + (i + 1) * col_width + col_width // 2, total_y + 20))
        surface.blit(total_surf, total_rect)


# 绘制游戏结束画面
def draw_game_over(surface, game):
    # 绘制背景面板
    pygame.draw.rect(surface, PANEL_COLOR, (WIDTH // 2 - 450, 50, 900, 400), border_radius=20)  # 扩大面板

    # 标题
    title = "游戏结束 - 最终结果"
    title_surf = title_font.render(title, True, ACCENT_COLOR)  # 使用强调色
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 100))
    surface.blit(title_surf, title_rect)

    # 统计数据
    stats = [
        f"总利润: ￥{game.total_profit}",
        f"总社会成本: ￥{int(game.total_social_cost)}",
        f"社会福利: ￥{int(game.social_welfare)}"
    ]

    y_offset = 150
    for stat in stats:
        stat_surf = header_font.render(stat, True, TEXT_COLOR)
        stat_rect = stat_surf.get_rect(center=(WIDTH // 2, y_offset))
        surface.blit(stat_surf, stat_rect)
        y_offset += 70  # 增加行间距

    # 评价
    welfare_percent = (game.social_welfare + 500) / 1000 * 100
    if welfare_percent > 80:
        evaluation = "优秀！您实现了社会福利最大化"
        color = POSITIVE_COLOR
    elif welfare_percent > 60:
        evaluation = "良好！接近社会最优水平"
        color = HIGHLIGHT_COLOR
    elif welfare_percent > 40:
        evaluation = "及格！需要平衡利润与社会成本"
        color = NEUTRAL_COLOR
    else:
        evaluation = "不及格！过度生产导致市场失灵"
        color = WARNING_COLOR

    eval_surf = header_font.render(evaluation, True, color)
    eval_rect = eval_surf.get_rect(center=(WIDTH // 2, 340))
    surface.blit(eval_surf, eval_rect)

    # 提示
    hint = "社会最优策略：每轮生产60单位左右"
    hint_surf = normal_font.render(hint, True, NEUTRAL_COLOR)
    hint_rect = hint_surf.get_rect(center=(WIDTH // 2, 400))
    surface.blit(hint_surf, hint_rect)


# 主游戏循环
def main():
    global game, submit_button, reset_button

    running = True
    slider_rect = pygame.Rect(150, 250, WIDTH - 300, 50)  # 扩大滑块
    slider_dragging = False

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # 事件处理
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if game.round <= game.total_rounds:
                # 滑块拖动
                if event.type == MOUSEBUTTONDOWN:
                    if slider_rect.collidepoint(mouse_pos):
                        slider_dragging = True

                if event.type == MOUSEBUTTONUP:
                    slider_dragging = False

                # 提交按钮
                if submit_button.is_clicked(mouse_pos, event):
                    game.calculate_effects()
            else:
                # 重新开始按钮
                if reset_button.is_clicked(mouse_pos, event):
                    game = GameState()
                    submit_button = Button(WIDTH // 2 - 120, 750, 240, 70, "提交决策")

            if event.type == MOUSEMOTION and slider_dragging:
                rel_x = mouse_pos[0] - slider_rect.x
                game.production = max(0, min(100, int(rel_x / slider_rect.width * 100)))

        # 更新按钮状态
        if game.round <= game.total_rounds:
            submit_button.check_hover(mouse_pos)
        else:
            reset_button.check_hover(mouse_pos)

        # 绘制白色背景
        screen.fill(BACKGROUND)

        # 绘制标题
        title = "市场失灵：外部性挑战"
        title_surf = title_font.render(title, True, TEXT_COLOR)
        screen.blit(title_surf, (100, 40))  # 调整位置

        # 绘制副标题
        subtitle = "在追求利润的同时，请考虑您的生产决策对社会的影响"
        subtitle_surf = normal_font.render(subtitle, True, NEUTRAL_COLOR)
        screen.blit(subtitle_surf, (100, 110))  # 调整位置

        if game.round <= game.total_rounds:
            # 绘制回合进度
            draw_round_progress(screen, WIDTH - 120, 120, 70, game.round, game.total_rounds)  # 调整位置和大小

            # 绘制生产滑块
            slider_rect = draw_production_slider(screen, 150, 250, WIDTH - 300, game.production)  # 扩大滑块

            # 绘制指标卡片 - 调整为水平排列
            card_width = (WIDTH - 260) // 3  # 三张卡片等宽，留出更大边距
            card_height = 220  # 增加卡片高度
            draw_metric_card(screen, 70, 350, card_width, card_height, "个人利润", f"￥{game.production * 2}",
                             HIGHLIGHT_COLOR)

            # 计算预估社会成本
            estimated_pollution = game.cumulative_pollution + game.production * (1 + game.production / 100)
            estimated_social_cost = estimated_pollution * 1.2

            draw_metric_card(screen, 70 + card_width + 20, 350, card_width, card_height, "社会成本",
                             f"￥{int(estimated_social_cost)}", WARNING_COLOR)

            # 计算预估社会福利
            estimated_welfare = (game.total_profit + game.production * 2) - (
                    game.total_social_cost + estimated_social_cost)
            draw_metric_card(screen, 70 + 2 * (card_width + 20), 350, card_width, card_height, "社会福利",
                             f"￥{int(estimated_welfare)}", POSITIVE_COLOR)

            # 绘制历史图表 - 位置下移并扩大
            if game.round > 1:
                draw_history_chart(screen, 100, 600, WIDTH - 200, 250, game.round_history)  # 扩大图表

            # 绘制提交按钮
            submit_button.draw(screen)

            # 绘制决策提示
            prompt = f"决策：您计划在本轮生产多少单位产品？（0-100）"
            prompt_surf = normal_font.render(prompt, True, TEXT_COLOR)
            screen.blit(prompt_surf, (150, 200))  # 调整位置

        else:
            # 游戏结束面板（顶部）
            draw_game_over(screen, game)

            # 绘制历史图表（左下方）
            draw_history_chart(screen, 70, 500, 600, 350, game.round_history)  # 扩大图表

            # 绘制历史数据表格（右下方）- 使用修改后的版本
            draw_history_table(screen, 700, 500, 600, 350, game.round_history)  # 扩大表格

            # 重新开始按钮
            reset_button.rect.y = 870  # 下移按钮
            reset_button.draw(screen)

        pygame.display.flip()
        pygame.time.delay(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()