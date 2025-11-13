import os
import random
import string
import subprocess
import sys
import threading
from os import makedirs
from random import shuffle
from subprocess import Popen, PIPE
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from starlette.responses import StreamingResponse, JSONResponse

pyPath = "./python-submissions/"
cppPath = "./cpp-submissions/"
exePath = "./executable-submissions/"

compileTimeout = 10
testCode = "./examples/randomPlayer.py"

makedirs(pyPath, exist_ok=True)
makedirs(cppPath, exist_ok=True)
makedirs(exePath, exist_ok=True)

tournamentPassword = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])
print(f"The password to run the tournament is: {tournamentPassword}")

class ProgramHandler:
    def __init__(self, path: str, n: int, j: int) -> None:
        self.path = path
        self.n = n
        self.cards = set(range(1,16))

        if path.endswith(".py"):
            self.p = Popen([sys.executable, "-u", path], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, bufsize=1)
        else:
            self.p = Popen(path, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, bufsize=1)

        # Send initial input
        self.p.stdin.write(f"{n} {j}\n")
        self.p.stdin.flush()

    def sendSubmissions(self, g: list[int]) -> None:
        self.p.stdin.write(" ".join(map(str, g)) + "\n")
        self.p.stdin.flush()

    def sendWinnable(self, w: int) -> None:
        self.p.stdin.write(f"{w}\n")
        self.p.stdin.flush()

    def getOutput(self) -> int:
        result = self.p.stdout.readline()
        if result == "":
            # Check if the process died
            retcode = self.p.poll()
            if retcode is not None:
                err = self.p.stderr.read()
                raise Exception(f"Subprocess {self.path} exited with code {retcode}.\nStderr:\n{err}")
            else:
                raise Exception(f"No output received from subprocess {self.path}")
        resInt = -1
        try:
            resInt = int(result.strip())
        except:
            pass
        if resInt in self.cards:
            self.cards.remove(resInt)
            return resInt
        else:
            raise Exception(f"{result.strip()} is no valid output")

    def __del__(self):
        try:
            self.p.kill()
        except Exception:
            pass


def game(paths: list[str]):
    n = len(paths)
    programs = []
    for i, p in enumerate(paths):
        try:
            programs.append(ProgramHandler(p, n, i))
        except Exception as e:
            while programs:
                del programs[0]
            yield [-100 if i==j else 0 for j in range(n)], ["x" for _ in range(n)], 0, "Initialisation error: " + str(e)
            return

    scores = [0 for _ in programs]
    submissions = [0 for _ in programs]

    remainer = 0
    winnables = [-1,-2,-3,-4,-5,1,2,3,4,5,6,7,8,9,10]
    while winnables:
        currentWinnable = random.choice(winnables)
        winnables.remove(currentWinnable)

        for i, p in enumerate(programs):
            try:
                p.sendWinnable(currentWinnable + remainer)
            except Exception as e:
                while programs:
                    del programs[0]
                yield [-100 if i==j else 0 for j in range(n)], ["x" for _ in range(n)], 0, "Initialisation error: " + str(e)
                return

        for i, p in enumerate(programs):
            try:
                submissions[i] = p.getOutput()
            except Exception as e:
                while programs:
                    del programs[0]
                yield [-100 if i==j else 0 for j in range(n)], ["x" for _ in range(n)],0, "Initialisation error: " + str(e)
                return

        if winnables:
            for i, p in enumerate(programs):
                try:
                    p.sendSubmissions(submissions)
                except Exception as e:
                    while programs:
                        del programs[0]
                    yield [-100 if i==j else 0 for j in range(n)], ["x" for _ in range(n)],0, "Initialisation error: " + str(e)
                    return

        submissionCounts = {s:0 for s in range(1,16)}

        winnableSum = currentWinnable+remainer

        for submission in submissions:
            submissionCounts[submission] += 1

        if currentWinnable + remainer >= 0:
            for i in range(15,0,-1):
                if submissionCounts[i] == 1:
                    scores[submissions.index(i)] += winnableSum
                    remainer = 0
                    break
            else:
                remainer = winnableSum
        else:
            for i in range(1,16,1):
                if submissionCounts[i] == 1:
                    scores[submissions.index(i)] += winnableSum
                    remainer = 0
                    break
            else:
                remainer = winnableSum

        yield scores.copy(), submissions.copy(), winnableSum, None

    while programs:
        del programs[0]



def testProgram(path: str):
    for i in range(100):
        try:
            n = random.randint(2,100)
            k = random.randint(1,100)
            w = random.randint(1,100)
            j = random.randrange(0,n)

            paths = [(path if i == j else testCode) for i in range(n)]


            scores, err = None, None
            for gs in game(paths):
                scores, _, _, err = gs

            if err:
                yield False, err
            else:
                yield True, i+1

        except Exception as e:
            yield False, str(e) + " \n(either that's my fault or you messed up very badly)"
            return


def allPrograms():
    pys = [pyPath+f for f in os.listdir(pyPath) if os.path.isfile(os.path.join(pyPath, f)) and f.endswith(".py") and not f.endswith(".temp.py")]
    exes = [exePath+f for f in os.listdir(exePath) if os.path.isfile(os.path.join(exePath, f)) and not f.endswith(".temp")]
    return pys + exes


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def root():
    with open("index.html") as f:
        return f.read()

# PYTHON
@app.post("/upload.py", response_class=HTMLResponse)
def wrapperUploadPy(team: Annotated[str, Form()], file: UploadFile = File(...)):
    return StreamingResponse(uploadPy(team, file), media_type="html")

def uploadPy(team: Annotated[str, Form()], file: UploadFile = File(...)):
    with open("preset.html") as f:
        yield f.read()

    if team is None or team == "" or team.endswith(".temp") or team.endswith(".py"): yield "<h1>Fuck Off</h1> This team name is not valid."; return

    yield "<h2>Submitting python file</h2>"
    yield "<h4>Uploading ...</h4>"
    try:
        with open(pyPath + team + ".temp.py", "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        yield f"There was an error uploading the file:\n {e}"
        yield "<br><a href='/'><button>Return to start page</button></a></body></html>"
        return
    finally:
        file.file.close()

    yield "<p>Upload successful</p>"

    for t in testUpload(pyPath + team + ".temp.py"):
        value, ok = t
        yield value
        if not ok: return

    yield "<h3>Saving file</h3>"
    os.replace(pyPath + team + ".temp.py", pyPath + team + ".py")
    yield "<p>Saving successful<p>"

    yield "<h3>Done!<h3>"
    yield "<p>You can now return to start page.</p>"
    yield "<a href='/'><button>Return</button></a>"

    yield "</body></html>"
    return

# C++
@app.post("/upload.cpp", response_class=HTMLResponse)
def wrapperUploadCpp(team: Annotated[str, Form()], file: UploadFile = File(...)):
    return StreamingResponse(uploadCpp(team, file), media_type="html")

def uploadCpp(team: Annotated[str, Form()], file: UploadFile = File(...)):
    with open("preset.html") as f:
        yield f.read()

    if team is None or team == "" or team.endswith(".temp") or team.endswith(".py"): yield "<h1>Fuck Off</h1> This team name is not valid."; return

    yield "<h2>Submitting C++ file</h2>"
    yield "<h4>Uploading ...</h4>"
    try:
        with open(cppPath + team + ".cpp", "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        yield f"<p>There was an error uploading the file:</p><br><code>{e}</code>"
        yield "<br><a href='/'><button>Return to start page</button></a></body></html>"
        return
    finally:
        file.file.close()

    yield "<p>Upload successful</p>"
    yield "<h4>Compiling</h4>"
    yield "<p>Compilation successful</p>"
    es = ""
    try:
        subp = subprocess.run(f"g++ -std=c++20 -o {exePath}{team}.temp {cppPath}{team}.cpp",shell=True, capture_output=True, timeout=compileTimeout)
        es = subp.stderr.decode()
        subp.check_returncode()
    except Exception as e:
        yield f"<p>There was an error compiling the your code:</p><code style='color: red'>{e}</code><br><br><p>stderr:</p><code style='color: red'>{es}</code>"
        yield "<br><a href='/'><button>Return to start page</button></a></body></html>"
        return

    for t in testUpload(exePath + team + ".temp"):
        value, ok = t
        yield value
        if not ok: return

    yield "<h3>Saving file</h3>"
    os.replace(exePath + team + ".temp", exePath + team)
    yield "<p>Saving successful<p>"

    yield "<h3>Done!<h3>"
    yield "<p>You can now return to start page.</p>"
    yield "<a href='/'><button>Return</button></a>"

    yield "</body></html>"
    return

# EXECUTABLE
@app.post("/upload.exe", response_class=HTMLResponse)
def wrapperUploadExe(team: Annotated[str, Form()], file: UploadFile = File(...)):
    return StreamingResponse(uploadExe(team, file), media_type="html")

def uploadExe(team: Annotated[str, Form()], file: UploadFile = File(...)):
    with open("preset.html") as f:
        yield f.read()

    if team is None or team == "" or team.endswith(".temp") or team.endswith(".py"): yield "<h1>Fuck Off</h1> This team name is not valid."; return

    yield "<h2>Submitting executable</h2>"
    yield "<h4>Uploading ...</h4>"
    try:
        with open(exePath + team + ".temp", "wb") as f:
            f.write(file.file.read())
        subprocess.run(f"chmod +x {exePath}{team}.temp", shell=True, capture_output=True, timeout=compileTimeout, check=True)
    except Exception as e:
        yield f"<p>There was an error uploading the file:</p><br><code>{e}</code>"
        yield "<br><a href='/'><button>Return to start page</button></a></body></html>"
        return
    finally:
        file.file.close()

    yield "<p>Upload successful</p>"

    for t in testUpload(exePath + team + ".temp"):
        value, ok = t
        yield value
        if not ok: return

    yield "<h3>Saving file</h3>"
    os.replace(exePath + team + ".temp", exePath + team)
    yield "<p>Saving successful<p>"

    yield "<h3>Done!<h3>"
    yield "<p>You can now return to start page.</p>"
    yield "<a href='/'><button>Return</button></a>"

    yield "</body></html>"
    return

def testUpload(path):
    yield "<h4>Testing upload</h4>", True
    yield '<progress id="pb" max="100" value="0"></progress>', True
    yield "<script>pb = document.getElementById('pb')</script>", True

    for tr in testProgram(path):
        testSuccess, value = tr
        if testSuccess:
            yield f"<script>pb.value={value}</script>", True
        else:
            yield f"<p style='color:red'><b>Error<b> your programm didn't pass the tests. But created this Error:<br><code>{value}</code></p><p>Note that these tests shouldn't be a challenge but just find potential flaws in your code. Your code is tested in $100$ random games with $100$ rounds (every input your program gets, is an input that actually could occur in the game).</p>", True
            yield "<br><a href='/'><button>Return to start page</button></a></body></html>", False
            return

    yield "<p>All tests successful.<p>", True
    return


@app.get("/randomGameDisplay", response_class=HTMLResponse)
def randomGameDisplay():
    with open("random-game.html") as f:
        return f.read()


@app.get("/background.jpeg")
def loadgif():
    def iterfile():
        with open("./background.jpeg", mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="jpeg")

def getAllMatchUps(programs):
    for n in range(3,6):
        yield from getAllMatchUpsWithFixedSize(programs, n)

def getAllMatchUpsWithFixedSize(programs,n):
    if n > len(programs):
        return
    if n == 0:
        yield []
        return
    for program in programs:
        for matchUp in getAllMatchUpsWithFixedSize(set(programs)-{program}, n-1):
            yield matchUp + [program]


@app.get("/randomGame", response_class=JSONResponse)
def randomGame():
    programs = random.choice(list(getAllMatchUps(allPrograms())))

    names = [os.path.basename(f).removesuffix(".py") for f in programs]

    scoreList = []
    submissionList = []
    winnableList = []
    for gs in game(programs):
        scores, submissions, winnable, _ = gs
        scoreList.append(scores)
        submissionList.append(submissions)
        winnableList.append(winnable)
    return {"n":len(programs),"names":names,"score-list":scoreList, "submission-list":submissionList, "winnable-list":winnableList}


scores = {}
muCount = 0
playedGames = 0

class TournamentThread(threading.Thread):
    def __init__(self, mu):
        threading.Thread.__init__(self)
        self.mu = mu

    def run(self):
        global scores, playedGames
        gameScores = None
        for cs in game(self.mu):
            gameScores, _, _, _ = cs

        for i, s in enumerate(gameScores):
            scores[self.mu[i]] += s

        playedGames += 1


@app.get("/start-tournament", response_class=JSONResponse)
def startTournament(pw : str = ""):
    #if pw != tournamentPassword: return{"ok":False, "error":"Invalid password"}
    global scores, playedGames, muCount
    programs = allPrograms()
    scores = {p:0 for p in programs}
    if len(programs) <= 1: return {"ok":False, "error":"Too few players"};
    mus = list(getAllMatchUps(programs))
    shuffle(mus)
    muCount = len(mus)
    starterThread = threading.Thread()
    starterThread.run = lambda : [TournamentThread(mu).start() for mu in mus]
    starterThread.start()
    return {"ok":True}


@app.get("/tournament", response_class=JSONResponse)
def tournament():
    return {os.path.basename(f).removesuffix(".py"):s for f, s in scores.items()}


@app.get("/tournamentDisplay", response_class=HTMLResponse)
def tournamentDisplay():
    with open("tournament.html") as f:
        return f.read()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)