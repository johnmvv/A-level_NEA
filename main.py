import asyncio
from managers import *
import pygame
import time

class Main:
    async def main(self): # the function that runs the whole program
        pygame.init() #starts pygame up
        screen = pygame.display.set_mode((800,600)) #makes the window, standard size
        #set all the managers 
        event_manager = EventManager()
        display_manager = DisplayManager()
        train_manager = TrainManager()
        menu = Menu(screen)
        menu.current_screen()
        '''
        t = time.time()
        last_50_fps = [0]*50
        '''
        
        #start seaching for tains and updating their positions
        asyncio.create_task(train_manager.search(display_manager, screen))
        asyncio.create_task(train_manager.update_train_positions())
        
        #begin the program
        running = True
        while running:
            # check for events
            for event in pygame.event.get():
                try:
                    event_outcome = await event_manager.handle(event, display_manager, train_manager, menu, screen)
                    await display_manager.refresh(screen)
                except:
                    pass
            
            #get all the things to render, and render them
            tasks = await train_manager.render(display_manager)
            if tasks:
                train_manager.train_buttons = [] #reset buttons so hitboxes match with current positions only
                await asyncio.gather(*tasks)
                
            #display screen
            await display_manager.display(screen)
            train_manager.show(screen)
            menu.draw(screen)
            pygame.display.flip()
            '''
            last_50_fps.append(1/(time.time()-t))
            last_50_fps.pop(0)
            print(sum(last_50_fps)/50)
            t = time.time()'
            '''
            await asyncio.sleep(0)


asyncio.run(Main().main())