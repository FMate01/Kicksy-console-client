import requests, json, time, signal, sys, threading, hmac, hashlib, os
import base64, binascii

def json2str(post):
    preamble = '#'*50+'\n'
    try:
        parts = []
        text = post['description']
        while 1:
            parts.append(text[:40])
            text = text[40:]
            if not text:
                break
        id_ = f"<{post['_id']}>"
        date_ = f"[{post['createdAt']}]"
        owner = f"{post['ownerName']}"
        badge = f"({'tag' if not len(post['badge']) else post['badge']})"
        description = "# "+"       #\n# ".join(parts)
        description += ' '*(47-len(parts[-1]))+"#"
        attachment = ""
        if 'attachment' in post.keys():
            attachment = f"{'Attachment: https://media.kicksy.hu/'+post['attachment'] if 'attachment' in post.keys() else ''}"
        header1 = f"# {id_}{date_}"
        header1 += ' '*(49-len(header1))+"#"
        header2 = f"#{' '*10}{owner}{badge}"
        header2 += ' '*(49-len(header2))+"#"
        header = header1+'\n'+header2
        msg = f"{header}\n{preamble}{description}\n"
        if len(attachment):
            msg += f"{attachment}\n"
        return preamble+msg+preamble+"\n"
    except KeyError:
        header = f"# [{post['createdAt']}]{post['ownerName']}"
        header += ' '*(49-len(header))+"#"
        parts = []
        text = post['content']
        while 1:
            parts.append(text[:40])
            text = text[40:]
            if not text:
                break
        description = "# "+"       #\n# ".join(parts)
        description += ' '*(47-len(parts[-1]))+"#"
        return f"{preamble}{header}\n{preamble}{description}\n{preamble}"

class Client():
    def __init__(self, creds):
        self.category = "global"
        creds = json.load(open(creds, "r"))
        self.sess = requests.Session()
        self.tokens = self.sess.post('https://api.kicksy.hu/auth/login', data={'username': creds["username"],'password': creds["password"]}).json()
        if "accessToken" not in self.tokens.keys():
            print("Invalid credentials.")
            sys.exit(1)
        print("Login successfull.")
        print(self.tokens)
        self.expire = time.time()+15*60 # Access expiration
        self.uid = self.tokens['user']['_id']
        self.headers = {
            'Authorization': f"Bearer {self.tokens['accessToken']}"
        }
        
        
    def run(self):
        # Main event loop
        while 1:
            cmd = ""
            try:
                cmd = int(input(f"""{'#'*40}
#{' '*2}Command:{' '*28}#
#{' '*6}0: exit{' '*25}#
#{' '*6}1: list categories{' '*14}#
#{' '*6}2: list posts in category{' '*7}#
#{' '*6}3: list comments on a post{' '*6}#
#{' '*6}4: change category{' '*14}#
#{' '*6}5: write a post{' '*17}#
#{' '*6}6: comment on a post{' '*12}#
#{' '*6}7: like a post{' '*18}#
#{' '*6}8: delete a post{' '*16}#
{'#'*40}\n"""))
            except KeyboardInterrupt:
                self.logout("", "")
            except ValueError:
                continue
            if cmd == 0:
                self.logout("", "")
            elif cmd==1:
                os.system("clear")
                self.listCategories()
            elif cmd == 2:
                os.system("clear")
                self.getPosts(client.category)
            elif cmd == 3:
                os.system("clear")
                postID = input("Paste here the posts ID: ")
                self.getComments(postID)
            elif cmd == 4:
                os.system("clear")
                self.category = input("New category: ")
            elif cmd == 5:
                os.system("clear")
                postText = input("Text of the post: ")
                self.post(postText)
            elif cmd == 6:
                os.system("clear")
                postID = input("Paste here the posts ID: ")
                commentText = input("Text of the comment: ")
                self.postComment(postID, commentText)
            elif cmd == 7:
                os.system("clear")
                postID = input("Paste here the posts ID: ")
                self.likePost(postID)
            elif cmd == 8:
                os.system("clear")
                postID = input("Paste here the posts ID: ")
                self.deletePost(postID)
            else:
                pass
                
                
    def logout(self, asd, asd2):
        # Logout at the end of sessions
        self.sess.post('https://api.kicksy.hu/auth/logout', headers=self.headers, data={'token': self.tokens['refreshToken']})
        print("\rLogging out")
        sys.exit(0)
        
        
    def refresh(self):
        # Refresh access token
        while 1:
            if(abs(time.time()-self.expire)<5):
                self.tokens['accessToken'] = self.sess.post('https://api.kicksy.hu/auth/refresh', headers=self.headers, data={'token': self.tokens['refreshToken']}).json()['accessToken']
                self.expire = time.time()+15*60
                self.headers = {
                    'Authorization': f"Bearer {self.tokens['accessToken']}"
                }
            else:
                time.sleep(10)


    def getPosts(self, category: str):
        # Retrieving posts in self.category
        self.posts = self.sess.get(f'https://api.kicksy.hu/posts/{category}', headers=self.headers, timeout=2).json()['posts']
        print(f"Posts in {self.category}:")
        for post in self.posts:
            print(json2str(post))
            
            
    def listCategories(self):
        # Lists available categories
        categories = self.sess.get(f'https://api.kicksy.hu/posts/list/categories', headers=self.headers, timeout=2).json()['categories']
        print("\t"+"\n\t".join(categories))
        
        
    def getComments(self, postID):
        # Retrieve comments on a post <postID>
        post = self.sess.get(f'https://api.kicksy.hu/posts/single/{postID}', headers=self.headers, timeout=2).json()
        if len(post['paginatedComments']['results']):
            print(f"Comments on {post['post']['ownerName']}'s post:\n"+"\n".join([json2str(p) for p in post['paginatedComments']['results']]))
        else:
            print("No comment.")
            
            
    def post(self, text):
        # Write a post in self.category
        response = self.sess.post('https://api.kicksy.hu/posts/new', headers=self.headers, data={'description': text, 'category': self.category})
        print("Post posted.")
        
        
    def postComment(self, postID, text):
        # Post a comment on a post identified by <postID>
        response = self.sess.post(f'https://api.kicksy.hu/comments/new/{postID}', headers=self.headers, data={'content': text})
        print("Comment posted.")
        
        
    def likePost(self, postID):
        # Like a post identified by <postID>
        response = self.sess.get(f'https://api.kicksy.hu/posts/like/{postID}', headers=self.headers)
        print("Post liked.")
        
        
    def deletePost(self, postID):
        # Delete a post identified by <postID>
        response = self.sess.get(f'https://api.kicksy.hu/posts/delete/{postID}', headers=self.headers)
        print("Post deleted.")

client = Client('cred.json')
signal.signal(signal.SIGINT, client.logout)

t2 = threading.Thread(target=client.refresh)# thread to periodically refresh the access token.
t2.setDaemon(True)
t2.start()

client.run()
