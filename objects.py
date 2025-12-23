import pygame
import time
import sqlite3

class Button: # parent class, for formatting purposes
    def __init__(self, x, y):
        self.x = x
        self.y = y
        pass

    def show(self, screen):
        pass

    def clicked(self, event):
        pass

class TrainButton(Button): # a clickable train that is displayed on the map
    def __init__(self, x, y, radius, train):
        super().__init__(x,y)
        self._r = radius
        self._primary = (0,255,0) #green
        self.train = train

    def show(self, screen): # draws a circle, black outline green inside
        pygame.draw.circle(screen, (0,0,0), (self.x, self.y), self._r)
        pygame.draw.circle(screen, self._primary, (self.x, self.y), (self._r * 0.7))

    def clicked(self, event):
        return ((event.pos[0] - self.x)**2 + (event.pos[1]- self.y)**2)*0.5 <= self._r # if in cricle
    
class MenuButton(Button): # button for menu
    def __init__(self, x, y, width, height, text):
        super().__init__(x, y)
        self._width = width
        self._height = height
        self.text = text
        self._primary = (100,100,100) #colour of backgrounf, grey
        self._secondary = (255,255,255) #colour of text, white

    def show(self, screen):
        pygame.draw.rect(screen, self._primary, (self.x,self.y,self._width,self._height)) # rectangle, just under the width of the menu
        font = pygame.font.Font()
        text = font.render(self.text, True, self._secondary, self._primary)
        text_rect = text.get_rect(center=(self.x + self._width/2, self.y + self._height/2)) #this line is from the pygame docs
        screen.blit(text, text_rect)
    
    def clicked(self, event):
        #print(self.text)
        return 0 <= event.pos[0]-self.x <= self._width and 0 <= event.pos[1]-self.y <= self._height # if in box
    
class InputBox(MenuButton):
    def __init__(self, x, y, width, height, text):
        super().__init__(x, y, width, height, text)
        self.typing = False
        self.writtenText = ""
        self._surface = pygame.Surface((width, height))
        self._surface.fill(self._primary)
        self._cursor = False
    
    def show(self, screen):
        pygame.draw.rect(screen, self._primary, (self.x,self.y,self._width,self._height))
        font = pygame.font.Font()
        displayed_text = ""

        if self.writtenText != "":
            displayed_text += self.writtenText
        if self.typing:
            if int(time.strftime('%S'))%2 == 0: #flashes every other second
                displayed_text += "|" #flashing bar that
            else:
                displayed_text += " " #add a space so the text isn't shifting side to side every second
        if displayed_text == "":
            displayed_text = self.text
        text = font.render(displayed_text, True, self._secondary, self._primary) # got this bit from the python pygame docs
        text_rect = text.get_rect(center=(self.x + self._width/2, self.y + self._height/2))
        screen.blit(text, text_rect)
    
    def clicked(self, event):
        if super().clicked(event):
            self.typing = True #start typing
        return super().clicked(event)

    def is_active(self): #if typing
        return self.typing
    
    def take_input(self, event):
        match event.key:
            case pygame.K_BACKSPACE: #if backspace, remove a character
                if len(self.text) > 0:
                    self.writtenText = self.writtenText[:-1]
            case pygame.K_RETURN:
                self.typing = False
            case _:
                self.writtenText += event.unicode # event.name does not in fact work, unless you want a " " to be "Space"

class Table(MenuButton):
    def __init__(self, x, y, width, height, text, data):
        super().__init__(x, y, width, height, text)
        self._headers = text.split("/")
        self.data = data # [starttime, endtime, path] w/ path being a list
        self.displayed_data = data

    def show(self, screen):
        pygame.draw.rect(screen, self._primary, (self.x,self.y,self._width,self._height)) # background
        pygame.draw.rect(screen, self._secondary, (self.x,self.y,self._width//2,30), 2) # outlines for table headern left
        pygame.draw.rect(screen, self._secondary, (self.x+self._width//2,self.y,self._width//2,30), 2) # outlines for table header right
        pygame.draw.rect(screen, self._secondary, (self.x,self.y+30,self._width//2,self._height-30), 2) # outlines for table body left
        pygame.draw.rect(screen, self._secondary, (self.x+self._width//2,self.y+30,self._width//2,self._height-30), 2) # outlines for table body right
        font = pygame.font.Font() # this style of setting up text, with a rectangle etc. is sourced from the pygame docs
        text1 = font.render(self._headers[0], True, self._secondary, self._primary) # write the headers
        text_rect = text1.get_rect(center=(self.x + self._width/4, self.y + 15))
        screen.blit(text1, text_rect)
        text2 = font.render(self._headers[1], True, self._secondary, self._primary)
        text_rect = text2.get_rect(center=(self.x + 3*self._width/4, self.y + 15)) 
        screen.blit(text2, text_rect)
        for i in range(len(self.displayed_data)): # for each peice of data, write it to screen
            if 30*(i+1) > self._height:
                break
            font = pygame.font.Font()
            text1 = font.render(str(self.displayed_data[i][0]), True, self._secondary, self._primary)
            text_rect = text1.get_rect(center=(self.x + self._width/4, self.y + 30*(i+1) + 15))
            screen.blit(text1, text_rect)
            text2 = font.render(str(self.displayed_data[i][1]), True, self._secondary, self._primary)
            text_rect = text2.get_rect(center=(self.x + 3*self._width/4, self.y+ 30*(i+1) + 15))
            screen.blit(text2,text_rect)

    def clicked(self, event):
        if not 0 <= event.pos[0]-self.x <= self._width and 30<= event.pos[1]-self.y <= min(self._height,30*(1+len(self.displayed_data))): #if over a diplayed entry
            print("nah")
            return None
        for i in range(len(self.displayed_data)): 
            if 0 <= event.pos[1]-self.y-30*(i+1) <= 30:
                return self.displayed_data[i] # get the row clicked

class RoutingTable(Table):
    def clicked(self, event):
        row = super().clicked(event)
        if row:
            if isinstance(row[2][-1], tuple): # if from raptor
                self.displayed_data = []
                for item in row[2]:
                    self.displayed_data.append(item[0]) 
                self.displayed_data.pop()
                self.displayed_data.append(row[2][-1])
                self._headers = ["Station", "Time"]
            else:
                self.displayed_data = row[2] 
                self._headers = ["Station", "Time"]
        return row
    
