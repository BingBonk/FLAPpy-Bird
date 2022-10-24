import pygame
import random
import cv2
import mediapipe as mp
import math
import time

# Camera Stuffs
cap = cv2.VideoCapture(0)
flap = False
pTime = 0
counter = 0
mpPose = mp.solutions.pose
pose = mpPose.Pose()

pygame.init()
clock = pygame.time.Clock()
fps = 60

screen_width = 864
screen_height = 936

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("FLAPpy Bird")

run = True

# load images
bg = pygame.image.load('img/bg.png')
ground_img = pygame.image.load("img/ground.png")
button_image = pygame.image.load("img/restart.png")

# Define font
font = pygame.font.SysFont("Bahaus 93", 60)

# define colour

white = (255, 255, 255)

# define game variables
ground_scroll = 0
scroll_speed = 4
flying = False
game_over = False
pipe_gap = 150
pipe_frequency = 6000  # milliseconds
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
pass_pipe = False


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def reset_game():
    pipe_group.empty()
    flappy.rect.x = 100
    flappy.rect.y = int(screen_height / 2)
    score = 0
    return score


class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f'img/bird{num}.png')
            self.counter += 1
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.vel = 0
        self.clicked = False

    def update(self):
        if flying:
            # gravity
            self.vel += 0.5
            if self.vel > 8:
                self.vel = 8
            if self.rect.bottom < 768:
                self.rect.y += int(self.vel)

        if not game_over:
            # jump (to be changed greatly (evil laugh))
            if flap == True and self.clicked == False:
                self.clicked = True
                self.vel = -10
            if flap == False:
                self.clicked = False

            # Handle the idle animation
            self.counter += 1
            flap_cooldown = 5

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
            self.image = self.images[self.index]

            # Rotate the bird

            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("img/pipe.png")
        self.rect = self.image.get_rect()
        # position 1 is from the top, -1 is from the bottom
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipe_gap / 2)]
        if position == -1:
            self.rect.topleft = [x, y + int(pipe_gap / 2)]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()


class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()
        # check if mouse is over button
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True

        # draw button
        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action


bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()

flappy = Bird(100, int(screen_height / 2))

bird_group.add(flappy)

btm_pipe = Pipe(300, int(screen_height / 2), -1)
top_pipe = Pipe(300, int(screen_height / 2), 1)

# restart button index
button = Button(screen_width // 2 - 50, screen_height // 2 - 100, button_image)

while run:
    # Camera
    lmList = []
    ret, img = cap.read()
    width = int(cap.get(3))
    height = int(cap.get(4))
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(imgRGB)
    if results.pose_landmarks:
        for id, lm in enumerate(results.pose_landmarks.landmark):
            h, w, c = img.shape
            lmList.append([id, int(lm.x * w), int(lm.y * h)])
        right_12to14_Hor = abs(lmList[12][1] - lmList[14][1])
        right_12to14_Ver = abs(lmList[14][2] - lmList[12][2])
        flapAngleRIGHT = math.degrees(math.atan2(right_12to14_Hor, right_12to14_Ver))
        left_11to13_Hor = abs(lmList[11][1] - lmList[13][1])
        left_11to13_Ver = abs(lmList[13][2] - lmList[11][2])
        flapAngleLEFT = math.degrees(math.atan2(left_11to13_Hor, left_11to13_Ver))
        if flapAngleLEFT > 46 and flapAngleRIGHT > 46:
            flap = True
        else:
            flap = False

        cTime = time.time()
        camera_fps = 1 / (cTime - pTime)
        pTime = cTime
        pipe_frequency = (60 / camera_fps) * 1500

    # Flap Detection

    clock.tick(fps)
    # Draw Background
    screen.blit(bg, (0, 0))

    bird_group.draw(screen)
    bird_group.update()

    pipe_group.draw(screen)

    # Draw the ground
    screen.blit(ground_img, (ground_scroll, 768))

    # Check the score
    if len(pipe_group) > 0:
        if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.left \
                and bird_group.sprites()[0].rect.right < pipe_group.sprites()[0].rect.right \
                and pass_pipe == False:
            pass_pipe = True
        if pass_pipe == True:
            if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.right:
                score += 1
                pass_pipe = False
    draw_text(str(score), font, white, int(screen_width / 2), 20)

    # look for collisions
    if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) or flappy.rect.top < 0:
        game_over = True

    # Check if bird has hit ground
    if flappy.rect.bottom >= 768:
        game_over = True
        flying = False

    if not game_over and flying:
        # Generate new pipes
        time_now = pygame.time.get_ticks()
        if time_now - last_pipe > pipe_frequency:
            pipe_height = random.randint(-100, 100)
            btm_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, -1)
            top_pipe = Pipe(screen_width, int(screen_height / 2) + pipe_height, 1)
            pipe_group.add(btm_pipe)
            pipe_group.add(top_pipe)
            last_pipe = time_now

        # Scroll the ground
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0

        pipe_group.update()

    # check for gameover and reset
    if game_over == True:
        if button.draw():
            game_over = False
            score = reset_game()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and flying == False and game_over == False:
            flying = True
    pygame.display.update()

pygame.quit()
