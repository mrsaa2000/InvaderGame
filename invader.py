import enum
import os
import pygame
from pygame.locals import *
import random
import sys


SCR_RECT = Rect(0, 0, 600, 580)
FRAMERATE = 60
State = enum.Enum('State', 'START PLAY GAMEOVER')


def load_image(filename):
    """画像をロードしてimageを返す"""
    try:
        image = pygame.image.load(filename)
    except pygame.error as message:
        print('Cannot load image: {}'.format(filename))
        raise SystemExit(message)
    if image.get_colorkey():
        image = image.convert_alpha()
    else:
        image = image.convert()
    return image


def split_image(filename, n):
    """n枚に切ったimage_listを返す"""
    image = load_image(filename)
    width = image.get_width()
    height = image.get_height()
    split_width = width // n
    image_list = []
    for i in range(0, width, split_width):
        surface = pygame.Surface((split_width, height))
        surface.blit(image, (0, 0), (i, 0, split_width, height))
        surface.set_colorkey((0, 0, 0))
        image_list.append(surface)
    return image_list


class Player(pygame.sprite.Sprite):

    """プレイヤー"""

    speed = 5

    def __init__(self, bullets):
        super(Player, self).__init__(self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.left = SCR_RECT.width / 2
        self.rect.bottom = SCR_RECT.bottom
        self.bullets = bullets
        self.life = 3
        self.pause_time = 0

    def update(self):
        if self.pause_time:
            self.pause_time -= 1
            self.image = self.images[1]
            return
        self.image = self.images[0]
        pressed_key = pygame.key.get_pressed()
        if pressed_key[K_LEFT]:
            self.rect.move_ip(-self.speed, 0)
        elif pressed_key[K_RIGHT]:
            self.rect.move_ip(self.speed, 0)
        self.rect = self.rect.clamp(SCR_RECT)
        if pressed_key[K_SPACE]:
            if len(self.bullets.sprites()) == 0:
                Bullet(self.rect.center)


class Bullet(pygame.sprite.Sprite):

    """プレイヤーの弾"""

    speed = 10

    def __init__(self, pos):
        super(Bullet, self).__init__(self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.pause_time = 0

    def update(self):
        if self.pause_time:
            self.pause_time -= 1
            return
        self.rect.move_ip(0, -self.speed)
        if self.rect.top < 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):

    """
    エイリアン
    10点の敵
    """

    frame = 0
    prob_beam = 0.001

    def __init__(self, pos):
        super(Enemy, self).__init__(self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        # 移動先のy座標
        self.moved_height = self.rect.center[1] + self.rect.height
        self.speed = self.rect.width
        self.pause_time = 0
        self.update_time = 60
        self.update_timer = self.update_time
        self.move_flag = True
        self.downed_flag = False

    def update(self):
        if self.pause_time:
            self.pause_time -= 1
            return
        if self.update_timer == 0:
            self.update_timer = self.update_time
            if self.move_flag:
                self.rect.move_ip(self.speed, 0)
                self.downed_flag = False
            else:
                self.move_down()
                self.update_time -= 3
                self.downed_flag = True
                self.speed = -self.speed
                self.move_flag = True
            self.image = self.images[self.frame % 2]
            self.frame += 1
            self.moved_height = self.rect.center[1] + self.rect.height
        self.update_timer -= 1
        # ランダムでビームを発射
        if self.prob_beam > random.random():
            Beam(self.rect.center)

    def move_down(self):
        self.rect.center = (self.rect.center[0], self.moved_height)


class Enemy20(Enemy):

    """20点の敵"""

    def __init__(self, pos):
        super(Enemy20, self).__init__(pos)


class Enemy30(Enemy):

    """30点の敵"""

    def __init__(self, pos):
        super(Enemy30, self).__init__(pos)


class Beam(pygame.sprite.Sprite):

    """エイリアンの弾"""

    speed = 5

    def __init__(self, pos):
        super(Beam, self).__init__(self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.pause_time = 0

    def update(self):
        if self.pause_time:
            self.pause_time -= 1
            return
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom > SCR_RECT.height:
            self.kill()


class Explosion(pygame.sprite.Sprite):

    """爆発エフェクト"""

    ani_cycle = 5
    frame = 0

    def __init__(self, pos):
        super(Explosion, self).__init__(self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.max_frame = len(self.images) * self.ani_cycle

    def update(self):
        self.image = self.images[self.frame // self.ani_cycle]
        self.frame += 1
        if self.frame == self.max_frame:
            self.kill()


class Torchka(pygame.sprite.Sprite):

    """トーチカ"""

    def __init__(self, pos):
        super(Torchka, self).__init__(self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.count = 0

    def update(self):
        if self.count > 3:
            self.kill()
        else:
            self.image = self.images[self.count]


class Game(object):

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCR_RECT.size)
        self.load_images()
        self.init_game()

        clock = pygame.time.Clock()
        while True:
            clock.tick(FRAMERATE)
            self.draw()
            self.update()
            self.event_handler()
            pygame.display.update()

    def init_game(self):
        """ゲームオブジェクトを初期化"""
        self.game_state = State.START
        self.score = 0
        self.stage = 0
        # sprite group
        self.all = pygame.sprite.RenderUpdates()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.beams = pygame.sprite.Group()
        self.torchkas = pygame.sprite.Group()
        Player.containers = self.all
        Bullet.containers = self.all, self.bullets
        Enemy.containers = self.all, self.enemies
        Enemy20.containers = self.all, self.enemies
        Enemy30.containers = self.all, self.enemies
        Beam.containers = self.all, self.beams
        Explosion.containers = self.all
        Torchka.containers = self.all, self.torchkas
        # プレイヤーを作成
        self.player = Player(self.bullets)
        # 敵を作成
        self.set_enemy()
        # トーチカを作成
        self.set_torchka((104, 500))
        self.set_torchka((224, 500))
        self.set_torchka((344, 500))
        self.set_torchka((464, 500))

    def set_enemy(self):
        """敵を設置"""
        start_height = (self.stage % 8 + 1) * 48
        for y in range(5):
            for x in range(10):
                if y == 0:
                    Enemy30((x * 30 + 36, y * 30 + start_height))
                elif y == 1 or y == 2:
                    Enemy20((x * 30 + 36, y * 30 + start_height))
                elif y == 3 or y == 4:
                    Enemy((x * 30 + 36, y * 30 + start_height))

    def set_torchka(self, pos):
        for y in range(2):
            for x in range(3):
                if not (y == 1 and x == 1):
                    Torchka((pos[0] + x * 16, pos[1] + y * 16))

    def update_enemy(self):
        """敵全体の動き"""
        for enemy in self.enemies.sprites():
            if enemy.rect.bottom > SCR_RECT.height * 0.9:
                self.game_state = State.GAMEOVER
            moved_left, moved_right = (enemy.rect.left - enemy.rect.width,
                                       enemy.rect.right + enemy.rect.width)
            if moved_left < 0 or moved_right >= SCR_RECT.width:
                if enemy.update_timer == 0:
                    if not enemy.downed_flag:  # 1段下に下りた後でなければ
                        for e in self.enemies.sprites():
                            e.move_flag = False
                        break

    def update(self):
        """ゲーム状態の更新"""
        if self.game_state == State.PLAY:
            # スプライトの更新
            self.all.update()
            self.update_enemy()
            # 衝突判定
            self.collision_detection()
        if len(self.enemies.sprites()) == 0:
            self.stage += 1
            self.set_enemy()

    def draw(self):
        """画面描画"""
        self.screen.fill((0, 0, 0))
        if self.game_state == State.START:
            self.draw_start()
        elif self.game_state == State.PLAY:
            self.draw_play()
        elif self.game_state == State.GAMEOVER:
            self.draw_gameover()

    def draw_start(self):
        """タイトル画面"""
        title_font = pygame.font.SysFont(None, 70)
        push_font = pygame.font.SysFont(None, 30)
        title = title_font.render('INVADER GAME', True, (255, 255, 255))
        push = push_font.render('PUSH SPACEKEY', True, (255, 255, 255))
        self.screen.blit(title, ((SCR_RECT.width - title.get_width()) / 2, 100))
        self.screen.blit(push, ((SCR_RECT.width - push.get_width()) / 2, 300))

    def draw_play(self):
        """ゲーム画面"""
        self.all.draw(self.screen)
        score_font = pygame.font.SysFont(None, 30)
        stage_font = pygame.font.SysFont(None, 30)
        life_font = pygame.font.SysFont(None, 30)
        score = score_font.render('SCORE: {}'.format(str(self.score)),
                                  True, (255, 255, 255))
        stage = stage_font.render('STAGE: {}'.format(str(self.stage + 1)),
                                  True, (255, 255, 255))
        life = life_font.render('LIFE:', True, (255, 255, 255))
        self.screen.blit(score, (0, 0))
        self.screen.blit(stage, (0, score.get_height()))
        self.screen.blit(life, (SCR_RECT.width - 82 - life.get_width(), 0))
        # ライフ表示
        for i in range(self.player.life):
            self.screen.blit(self.player_imgs[0], ((SCR_RECT.width - 78) + 26 * i, 0))

    def draw_gameover(self):
        """ゲームオーバー画面"""
        gameover_font = pygame.font.SysFont(None, 70)
        push_font = pygame.font.SysFont(None, 30)
        gameover = gameover_font.render('GAME OVER', True, (255, 255, 255))
        push = push_font.render('PUSH SPACEKEY', True, (255, 255, 255))
        self.screen.blit(gameover, ((SCR_RECT.width - gameover.get_width()) / 2,
                                    (SCR_RECT.height - gameover.get_height()) / 2))
        self.screen.blit(push, ((SCR_RECT.width - push.get_width()) / 2, 350))

    def collision_detection(self):
        """衝突判定"""
        # 敵とプレイヤーの弾
        enemy_collided = pygame.sprite.groupcollide(self.enemies, self.bullets,
                                                    True, True)
        for enemy in enemy_collided.keys():
            Explosion(enemy.rect.center)
            # 敵撃破でスコア追加
            if enemy.__class__.__name__ == 'Enemy30':
                self.score += 30
            elif enemy.__class__.__name__ == 'Enemy20':
                self.score += 20
            elif enemy.__class__.__name__ == 'Enemy':
                self.score += 10
        # プレイヤーと敵のビーム
        beam_collided = pygame.sprite.spritecollide(self.player, self.beams, True)
        if beam_collided:
            if self.player.life == 0:
                self.player.kill()
                self.game_state = State.GAMEOVER
            else:
                self.player.life -= 1
                Explosion(self.player.rect.center)
                for sprite in self.all.sprites():
                    sprite.pause_time = 20
        # トーチカ
        torchka_bullet_collided = pygame.sprite.groupcollide(self.torchkas,
                                                             self.bullets,
                                                             False, True)
        for torchka in torchka_bullet_collided.keys():
            torchka.count += 1
        torchka_beam_collided = pygame.sprite.groupcollide(self.torchkas,
                                                           self.beams,
                                                           False, True)
        for torchka in torchka_beam_collided.keys():
            torchka.count += 1

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif event.type == KEYUP and event.key == K_SPACE:
                if self.game_state == State.START:
                    self.game_state = State.PLAY
                elif self.game_state == State.GAMEOVER:
                    self.init_game()
                    self.game_state = State.PLAY

    def load_images(self):
        self.player_imgs = split_image(os.path.join('img', 'player.png'), 2)
        Player.images = self.player_imgs
        Bullet.image = load_image(os.path.join('img', 'bullet.png'))
        Enemy.images = split_image(os.path.join('img', 'enemy10.png'), 2)
        Enemy20.images = split_image(os.path.join('img', 'enemy20.png'), 2)
        Enemy30.images = split_image(os.path.join('img', 'enemy30.png'), 2)
        Beam.image = load_image(os.path.join('img', 'beam.png'))
        Explosion.images = split_image(os.path.join('img', 'explosion.png'), 4)
        Torchka.images = split_image(os.path.join('img', 'torchka.png'), 4)


if __name__ == '__main__':
    Game()
