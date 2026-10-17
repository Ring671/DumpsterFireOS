import os,sys,tempfile,subprocess,ctypes,shutil,zipfile,io,sqlite3,posixpath
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from PySide6.QtCore import Qt,QUrl,QSize,QTimer,Signal
from PySide6.QtGui import QAction,QKeySequence,QFont,QIcon,QPixmap,QPainter,QColor
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QLineEdit,QPlainTextEdit,QSplitter,QToolButton,QFrame,QMdiArea,QMdiSubWindow,QListWidget,QListWidgetItem,QTabWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage,QWebEngineDownloadRequest
A=Path(__file__).resolve().parent/'Assets'
X='.png','.ico','.jpg','.jpeg','.webp','.bmp'
def blank():A=QPixmap(1,1);A.fill(Qt.GlobalColor.transparent);return QIcon(A)
def icon(n,s=None,crop=False):
	for C in[A/n]+[A/f"{n}{B}"for B in X]:
		if not C.is_file():continue
		B=QPixmap(str(C))
		if B.isNull():continue
		if s:
			D=Qt.AspectRatioMode.KeepAspectRatioByExpanding if crop else Qt.AspectRatioMode.KeepAspectRatio;B=B.scaled(QSize(s,s),D,Qt.TransformationMode.SmoothTransformation)
			if crop:B=B.copy(max(0,(B.width()-s)//2),max(0,(B.height()-s)//2),s,s)
		return QIcon(B)
def app_icon():return icon('OS_Icon')or blank()
def clean(n):n=posixpath.basename(str(n).replace('\\','/').strip());return''if n in('.','..')else n
class Wall(QWidget):
	def __init__(A,p):super().__init__();A.w=QPixmap(str(p))
	def paintEvent(A,_):B=QPainter(A);B.fillRect(A.rect(),QColor('#0a1a27'))if A.w.isNull()else B.drawPixmap(A.rect(),A.w)
def battery():
	try:
		import psutil as E
		if(C:=E.sensors_battery())is not None:return int(C.percent),bool(C.power_plugged)
	except Exception:0
	try:
		if sys.platform=='win32':
			class F(ctypes.Structure):_fields_=[('a',ctypes.c_ubyte),('f',ctypes.c_ubyte),('p',ctypes.c_ubyte),('s',ctypes.c_ubyte),('l',ctypes.c_ulong),('fl',ctypes.c_ulong)]
			A=F()
			if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(A))and A.p<=100 and not A.f&128:return int(A.p),A.a==1
		elif sys.platform.startswith('linux'):
			for D in Path('/sys/class/power_supply').glob('BAT*'):return int((D/'capacity').read_text()),(D/'status').read_text().strip()!='Discharging'
		elif sys.platform=='darwin':
			B=subprocess.run(['pmset','-g','batt'],capture_output=True,text=True,timeout=3).stdout
			if'%'in B:return int(B.split('%')[0].split()[-1]),'discharging'not in B
	except Exception:0
def net():
	try:
		from PySide6.QtNetwork import QNetworkInformation as A
		if A.instance()is None:A.loadDefaultBackend()
		B=A.instance()
		if B is None:return'Wi-Fi: ?'
		if B.reachability()==A.Reachability.Disconnected:return'Wi-Fi: Off'
		if A.Feature.TransportMedium in B.supportedFeatures():
			C=B.transportMedium()
			if C==A.TransportMedium.WiFi:return'Wi-Fi: On'
			if C==A.TransportMedium.Ethernet:return'Ethernet'
		return'Online'
	except Exception:return'Wi-Fi: ?'
class Tray(QFrame):
	def __init__(A):
		super().__init__(objectName='statusTray');B=QHBoxLayout(A);B.setContentsMargins(6,0,6,0);B.setSpacing(8);A.wifi,A.bat,A.clock=QLabel(),QLabel(),QLabel()
		for C in(A.wifi,A.bat,A.clock):C.setObjectName('statusLabel');B.addWidget(C)
		A.tick();A.sys();QTimer(A,interval=1000,timeout=A.tick).start();QTimer(A,interval=10000,timeout=A.sys).start()
	def tick(B):A=datetime.now();B.clock.setText(A.strftime('%I:%M %p').lstrip('0')+'  '+A.strftime('%b %d').replace(' 0',' '));B.clock.setToolTip(A.strftime('%A, %B %d, %Y'))
	def sys(B):
		C=net();B.wifi.setText({'Wi-Fi: On':'Wi-Fi','Wi-Fi: Off':'Wi-Fi off'}.get(C,C.replace('Wi-Fi: ','')));B.wifi.setToolTip(C);A=battery();B.bat.setVisible(A is not None)
		if A:B.bat.setText(f"{A[0]}%"+('+'if A[1]else''));B.bat.setToolTip(f"Battery {A[0]}%"+(' (charging)'if A[1]else''))
class VFS:
	def __init__(A,db):A.d=sqlite3.connect(str(db));A.d.execute('CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, parent TEXT NOT NULL, name TEXT NOT NULL, is_dir INTEGER NOT NULL, size INTEGER NOT NULL DEFAULT 0, data BLOB)');A.d.execute('CREATE INDEX IF NOT EXISTS idx ON files(parent)');A.d.commit();A.mkdir('/Downloads')
	def n(A,p):return posixpath.normpath('/'+str(p).replace('\\','/').lstrip('/'))
	def join(A,f,n):return A.n(posixpath.join(A.n(f),n))
	def ex(A,p):p=A.n(p);return p=='/'or A.d.execute('SELECT 1 FROM files WHERE path=?',(p,)).fetchone()is not None
	def isd(A,p):
		p=A.n(p)
		if p=='/':return True
		B=A.d.execute('SELECT is_dir FROM files WHERE path=?',(p,)).fetchone();return bool(B and B[0])
	def mkdir(A,p):
		B=''
		for C in[A for A in A.n(p).split('/')if A]:
			B+='/'+C
			if not A.ex(B):A.d.execute('INSERT INTO files(path,parent,name,is_dir,size) VALUES(?,?,?,1,0)',(B,posixpath.dirname(B)or'/',C))
		A.d.commit()
	def ls(A,f):return A.d.execute('SELECT path,name,is_dir,size FROM files WHERE parent=? ORDER BY is_dir DESC,name COLLATE NOCASE',(A.n(f),)).fetchall()
	def py(A):return[A[0]for A in A.d.execute('SELECT path FROM files WHERE is_dir=0 AND lower(name) LIKE ? ORDER BY path',('%.py',)).fetchall()]
	def w(A,p,d):p=A.n(p);A.mkdir(posixpath.dirname(p)or'/');A.d.execute('INSERT OR REPLACE INTO files(path,parent,name,is_dir,size,data) VALUES(?,?,?,0,?,?)',(p,posixpath.dirname(p)or'/',posixpath.basename(p),len(d),sqlite3.Binary(d)));A.d.commit()
	def r(A,p):B=A.d.execute('SELECT data FROM files WHERE path=? AND is_dir=0',(A.n(p),)).fetchone();return None if B is None else bytes(B[0]or b'')
	def rm(A,p):
		p=A.n(p)
		if p=='/':return
		B=p+'/';A.d.execute('DELETE FROM files WHERE path=? OR substr(path,1,?)=?',(p,len(B),B));A.d.commit()
	def mv(A,o,n):
		o,n=A.n(o),A.n(n);B=o+'/';E=A.d.execute('SELECT path FROM files WHERE substr(path,1,?)=?',(len(B),B)).fetchall();A.d.execute('UPDATE files SET path=?,parent=?,name=? WHERE path=?',(n,posixpath.dirname(n)or'/',posixpath.basename(n),o))
		for(C,)in E:D=n+C[len(o):];A.d.execute('UPDATE files SET path=?,parent=? WHERE path=?',(D,posixpath.dirname(D)or'/',C))
		A.d.commit()
	def uniq(A,f,n):
		n=clean(n)or'file';D,E=posixpath.splitext(n);B,C=A.join(f,n),1
		while A.ex(B):B=A.join(f,f"{D} ({C}){E}");C+=1
		return B
class TBtn(QToolButton):
	def __init__(A):super().__init__();A.o=False
	def set_open(A,v):A.o=bool(v);A.update()
	def paintEvent(A,e):
		super().paintEvent(e)
		if A.o:B=QPainter(A);B.setRenderHint(QPainter.RenderHint.Antialiasing);B.setPen(Qt.PenStyle.NoPen);B.setBrush(QColor('#4da3ff'));B.drawEllipse(A.width()//2-3,A.height()-7,6,6)
class Win(QMdiSubWindow):
	shown_changed=Signal(bool)
	def __init__(A):super().__init__();A._c=False;A.setMinimumSize(320,220)
	def showEvent(A,e):super().showEvent(e);A.shown_changed.emit(True)
	def hideEvent(A,e):super().hideEvent(e);A.shown_changed.emit(False)
	def closeEvent(A,e):e.ignore();A.hide()
	def clamp(A):
		B=A.mdiArea()
		if B is None or A._c:return
		A._c=True;C=B.viewport().rect();D=min(max(A.x(),40-A.width()),C.width()-40);E=min(max(A.y(),0),C.height()-30)
		if(D,E)!=(A.x(),A.y()):A.move(D,E)
		A._c=False
	def moveEvent(A,e):super().moveEvent(e);A.clamp()
class WS(QMdiArea):
	def __init__(A):super().__init__();A.base=None;A.subWindowActivated.connect(lambda _:A.fit())
	def set_base(A,w):A.base=w;w.setParent(A.viewport());w.lower();w.show();A.fit()
	def fit(A):
		if A.base:A.base.setGeometry(A.viewport().rect());A.base.lower()
	def resizeEvent(A,e):
		super().resizeEvent(e);A.fit()
		for B in A.subWindowList():
			if isinstance(B,Win):B.clamp()
class Page(QWebEnginePage):
	def __init__(A,parent=None,nt=None):super().__init__(parent);A.nt=nt
	def createWindow(A,_):return A.nt()if A.nt else A
class OS(QMainWindow):
	def __init__(B):
		super().__init__();B.setWindowTitle('Dumpster fire OS');B.setWindowIcon(app_icon());B.resize(1000,650)
		for H in Path(tempfile.gettempdir()).glob('dfos_*'):shutil.rmtree(H,ignore_errors=True)
		B.vfs=VFS(Path(__file__).resolve().parent/'Storage.db');B.folder='/';B.code=None;F=QWidget();C=QVBoxLayout(F);C.setContentsMargins(0,0,0,0);C.setSpacing(0);B.M=WS();B.M.setObjectName('windowWorkspace');B.M.setViewMode(QMdiArea.ViewMode.SubWindowView);B.M.setBackground(QColor('#0a1a27'));B.M.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);B.M.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);C.addWidget(B.M,1);B.taskbar(C);B.setCentralWidget(F);B.desk=Wall(A/'DesktopWallpaper.png');B.br,B.st,B.fl=QWidget(),QWidget(),QWidget();B.deskUI();B.M.set_base(B.desk);B.brUI();B.stUI();B.flUI();B.W,B.PW={},{}
		for(E,(G,I,J))in{'Duck Duck Go':(B.br,QSize(850,540),(55,45)),'Python Studio':(B.st,QSize(850,540),(90,70)),'Files':(B.fl,QSize(700,460),(125,95))}.items():D=B.mkwin(G,E,I);D.move(*J);D.shown_changed.connect(B.tb[E].set_open);B.W[E]=D;B.PW[G]=D
	def btn(B,L,t,a):A=QPushButton(t);A.clicked.connect(a);L.addWidget(A);return A
	def tbar(B,L,t):A=QHBoxLayout();A.addWidget(QLabel(t));A.addStretch();L.addLayout(A)
	def mkwin(B,w,t,z):A=Win();A.setWidget(w);A.setWindowTitle(t);A.setWindowIcon(blank());A.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose,False);A.resize(z);B.M.addSubWindow(A);A.hide();return A
	def act(B,p):
		if p is B.desk:return B.show_desk()
		A=B.PW.get(p)
		if not A:return
		if A.isMinimized()or A.isMaximized():A.showNormal()
		A.show();A.clamp();A.raise_();A.setFocus();B.M.setActiveSubWindow(A)
	def show_desk(A):
		for B in A.W.values():B.hide()
	def taskbar(B,L):
		D=QFrame(objectName='taskbar');D.setFixedHeight(44);C=QHBoxLayout(D);C.setContentsMargins(8,4,8,4);C.setSpacing(6);B.tb={}
		for(E,F,G)in(('Duck Duck Go','DuckDuckGo',lambda:B.act(B.br)),('Python Studio','Python_Studio',lambda:B.act(B.st)),('Files','Folder_Icon',lambda:B.act(B.fl))):A=TBtn();B.tb[E]=A;A.setObjectName('taskAppButton');A.setIcon(icon(F,28)or blank());A.setIconSize(QSize(28,28));A.setFixedSize(38,38);A.setToolTip(E);A.setCursor(Qt.CursorShape.PointingHandCursor);A.clicked.connect(G);C.addWidget(A)
		C.addStretch();C.addWidget(Tray());L.addWidget(D)
	def deskUI(B):
		B.desk.setObjectName('desktop');C=QVBoxLayout(B.desk);C.setContentsMargins(18,16,18,16);C.setSpacing(12);D=QHBoxLayout();D.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop);D.setSpacing(10)
		for(E,F,G)in(('Duck Duck Go','DuckDuckGo',lambda:B.act(B.br)),('Python Studio','Python_Studio',lambda:B.act(B.st)),('Files','Folder_Icon',lambda:B.act(B.fl))):A=QToolButton();A.setText(E);A.setIcon(icon(F,36,True)or blank());A.setIconSize(QSize(36,36));A.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon);A.setFixedSize(100,92);A.setObjectName('desktopShortcut');A.setCursor(Qt.CursorShape.PointingHandCursor);A.clicked.connect(G);D.addWidget(A)
		C.addLayout(D);C.addStretch()
	def brUI(A):
		B=QVBoxLayout(A.br);B.setContentsMargins(6,6,6,6);B.setSpacing(4);A.tbar(B,'Duck Duck Go');D=QHBoxLayout();A.url=QLineEdit(placeholderText='Website or search...');A.url.returnPressed.connect(A.go)
		for(G,E)in(('Back',lambda:A.vcall('back')),('Forward',lambda:A.vcall('forward')),('Reload',lambda:A.vcall('reload')),('Go',A.go)):A.btn(D,G,E)
		D.addWidget(A.url,1);B.addLayout(D);A.tabs=QTabWidget(objectName='browserTabs');A.tabs.setTabsClosable(True);A.tabs.setMovable(True);A.tabs.setDocumentMode(True);A.tabs.tabCloseRequested.connect(A.ctab);A.tabs.currentChanged.connect(A.tabc);C=QToolButton(objectName='newTabButton',text='+',toolTip='New tab (Ctrl+T)');C.setCursor(Qt.CursorShape.PointingHandCursor);C.setFixedSize(24,22);C.clicked.connect(A.ntab);A.tabs.setCornerWidget(C,Qt.Corner.TopRightCorner);B.addWidget(A.tabs,1)
		for(H,E)in(('Ctrl+T',A.ntab),('Ctrl+W',A.ctabc),('Ctrl+L',lambda:(A.url.setFocus(),A.url.selectAll()))):F=QAction(A.br);F.setShortcut(QKeySequence(H));F.triggered.connect(E);A.br.addAction(F)
		A.ntab()
	def cur(A):return A.tabs.currentWidget()if A.tabs.count()else None
	def vcall(B,m):
		A=B.cur()
		if A:getattr(A,m)()
	def addtab(B,u=None):
		A=QWebEngineView();A.setPage(Page(A,nt=B.mkpage));A.page().renderProcessTerminated.connect(lambda*A,x=A:x.reload());A.page().profile().downloadRequested.connect(B.dl);A.urlChanged.connect(lambda u,x=A:B.uch(x,u));A.titleChanged.connect(lambda t,x=A:B.tch(x,t));B.tabs.setCurrentIndex(B.tabs.addTab(A,'New Tab'))
		if u:A.setUrl(u)
		B.tabs.setTabsClosable(B.tabs.count()>1);return A
	def mkpage(A):return A.addtab().page()
	def ntab(A):A.addtab(QUrl('https://lite.duckduckgo.com/lite/'));A.url.setFocus();A.url.selectAll()
	def ctab(A,i):
		if A.tabs.count()<=1:return
		B=A.tabs.widget(i);A.tabs.removeTab(i)
		if B:B.deleteLater()
		A.tabs.setTabsClosable(A.tabs.count()>1)
	def ctabc(A):A.ctab(A.tabs.currentIndex())
	def tabc(A,_):
		B=A.cur()
		if B:A.url.setText(B.url().toString())
	def uch(A,v,u):
		if v is A.cur():A.url.setText(u.toString())
	def tch(B,v,t):
		C=B.tabs.indexOf(v)
		if C<0:return
		A=(t or'New Tab').strip()
		if len(A)>22:A=A[:21]+'…'
		B.tabs.setTabText(C,A);B.tabs.setTabToolTip(C,t or'')
	def go(B):
		C=B.cur()or B.addtab();A=B.url.text().strip()
		if not A:return
		D=A.split('/')[0];E='https://lite.duckduckgo.com/lite/?q='+quote(A)if' 'in A or'.'not in D and'://'not in A else A if'://'in A else'https://'+A;B.act(B.br);C.setUrl(QUrl(E))
	def dl(C,d):A=clean(d.downloadFileName())or'download';B=tempfile.mkdtemp(prefix='dfos_dl_');d.setDownloadDirectory(B);d.setDownloadFileName(A);d.isFinishedChanged.connect(lambda*A,x=d,fo=B,nm=A:C.dlfin(x,fo,nm));d.accept()
	def dlfin(A,d,f,n):
		if not d.isFinished():return
		try:
			if d.state()==QWebEngineDownloadRequest.DownloadState.DownloadCompleted:B=Path(d.downloadDirectory())/d.downloadFileName();A.vfs.w(A.vfs.uniq('/Downloads',n),B.read_bytes())
		except(OSError,sqlite3.Error)as C:A.msg(f"Couldn't store {n}: {C}")
		finally:shutil.rmtree(f,ignore_errors=True)
		A.flref()
	def flUI(A):
		B=QVBoxLayout(A.fl);A.tbar(B,'Files');F=QHBoxLayout()
		for(H,I)in(('Up',A.fup),('New Folder',A.fnew),('Unzip',A.funz),('Rename',A.fren),('Delete',A.fdel)):A.btn(F,H,I)
		F.addStretch();B.addLayout(F);A.nf=QWidget();D=QHBoxLayout(A.nf);D.setContentsMargins(0,0,0,0);A.nfi=QLineEdit(placeholderText='New folder name...');A.nfi.returnPressed.connect(A.fmk);D.addWidget(A.nfi,1);A.btn(D,'Create',A.fmk);A.btn(D,'Cancel',A.nf.hide);A.nf.hide();B.addWidget(A.nf);A.delb=QWidget();E=QHBoxLayout(A.delb);E.setContentsMargins(0,0,0,0);A.dell=QLabel();E.addWidget(A.dell,1);A.btn(E,'Delete',A.fdelc);A.btn(E,'Cancel',A.fdelx);A.delb.hide();A.pdel=None;B.addWidget(A.delb);A.fpath=QLabel();B.addWidget(A.fpath);A.fll=QListWidget();A.fll.itemDoubleClicked.connect(A.fopen);B.addWidget(A.fll,1);A.fdir='/';A.rb=QWidget();C=QHBoxLayout(A.rb);C.setContentsMargins(0,0,0,0);C.addWidget(QLabel('New name:'));A.rin=QLineEdit();A.rin.returnPressed.connect(A.doren);C.addWidget(A.rin,1);A.btn(C,'Rename',A.doren);A.btn(C,'Cancel',A.rb.hide);A.rb.hide();B.addWidget(A.rb);A.mb=QWidget();G=QHBoxLayout(A.mb);G.setContentsMargins(0,0,0,0);A.ml=QLabel();A.ml.setWordWrap(True);G.addWidget(A.ml,1);A.btn(G,'OK',A.mb.hide);A.mb.hide();B.addWidget(A.mb);A.flref()
	def flref(A):
		if not A.vfs.isd(A.fdir):A.fdir='/'
		A.fll.clear();A.fpath.setText('Storage'+(''if A.fdir=='/'else A.fdir))
		for(E,B,F,C)in A.vfs.ls(A.fdir):G='[Folder]  '+B if F else f"{B}   ({C/1048576:.1f} MB)"if C/1024>=1024 else f"{B}   ({C/1024:.1f} KB)";D=QListWidgetItem(G);D.setData(Qt.ItemDataRole.UserRole,E);A.fll.addItem(D)
	def fsel(B):A=B.fll.currentItem();return A.data(Qt.ItemDataRole.UserRole)if A else None
	def fopen(A,i):
		B=i.data(Qt.ItemDataRole.UserRole)
		if A.vfs.isd(B):A.fdir=B;A.flref()
		elif B.lower().endswith('.zip'):A.funz()
		elif B.lower().endswith('.py'):A.ld(B)
	def fup(A):
		if A.fdir!='/':A.fdir=posixpath.dirname(A.fdir)or'/';A.flref()
	def fnew(A):A.nfi.clear();A.nf.show();A.nfi.setFocus()
	def fmk(A):
		C=clean(A.nfi.text())
		if not C:return
		B=A.vfs.join(A.fdir,C)
		if A.vfs.ex(B):A.msg('That name already exists.');return
		A.vfs.mkdir(B);A.nf.hide();A.flref();A.fselp(B)
	def fselp(A,p):
		for C in range(A.fll.count()):
			B=A.fll.item(C)
			if B.data(Qt.ItemDataRole.UserRole)==p:A.fll.setCurrentItem(B);return
	def unz(A,z):
		B=A.vfs.uniq(posixpath.dirname(z)or'/',posixpath.splitext(posixpath.basename(z))[0])
		try:
			with zipfile.ZipFile(io.BytesIO(A.vfs.r(z)))as E:
				A.vfs.mkdir(B)
				for D in E.infolist():
					C=[A for A in D.filename.replace('\\','/').split('/')if A not in('','.')]
					if'..'in C:raise ValueError('The zip contains an unsafe path.')
					if not C or C[0]=='__MACOSX':continue
					F=A.vfs.join(B,'/'.join(C))
					if D.is_dir():A.vfs.mkdir(F)
					else:A.vfs.w(F,E.read(D))
		except(zipfile.BadZipFile,ValueError,OSError,RuntimeError,sqlite3.Error)as G:A.vfs.rm(B);A.msg(f"Couldn't unzip {posixpath.basename(z)}: {G}");return
		return B
	def funz(A):
		B=A.fsel()
		if B is None or not B.lower().endswith('.zip'):A.msg('Select a .zip file to unzip.');return
		C=A.unz(B);A.flref()
		if C:A.fselp(C)
	def msg(A,t):A.ml.setText(t);A.mb.show()
	def fren(A):
		B=A.fsel()
		if B is None:return
		A.rt=B;A.rin.setText(posixpath.basename(B));A.rin.selectAll();A.rb.show();A.rin.setFocus()
	def doren(A):
		B=A.rt;C=clean(A.rin.text())
		if not C or C==posixpath.basename(B):A.rb.hide();return
		D=A.vfs.join(posixpath.dirname(B),C)
		if A.vfs.ex(D):A.msg('That name already exists.');return
		A.vfs.mv(B,D);A.rb.hide();A.flref();A.fselp(D)
	def fdel(A):
		B=A.fsel()
		if B is None:return
		A.pdel=B;A.dell.setText(f"Delete {posixpath.basename(B)}? This can't be undone.");A.delb.show()
	def fdelx(A):A.pdel=None;A.delb.hide()
	def fdelc(A):
		B,A.pdel=A.pdel,None;A.delb.hide()
		if B:A.vfs.rm(B)
		A.flref()
	def stUI(A):
		C=QVBoxLayout(A.st);A.tbar(C,'Python Studio');D=QHBoxLayout();A.fnl=QLabel('Untitled.py');D.addWidget(A.fnl);D.addStretch()
		for(K,I)in(('New',A.ncode),('Open',A.chcode),('Save',A.save),('Save As',A.saveas),('Run',A.run)):A.btn(D,K,I)
		C.addLayout(D);E=QSplitter(Qt.Orientation.Vertical);A.ed=QPlainTextEdit();A.ed.setFont(QFont('Consolas',11));A.ed.setPlainText('print("Welcome to Dumpster fire OS!")');E.addWidget(A.ed);A.out=QPlainTextEdit();A.out.setReadOnly(True);A.out.setFont(QFont('Consolas',10));E.addWidget(A.out);E.setSizes([400,180]);C.addWidget(E,1);A.stat=QLabel('Ready');C.addWidget(A.stat);A.sb=QWidget();B=QHBoxLayout(A.sb);B.setContentsMargins(0,0,0,0);B.addWidget(QLabel('Folder:'));A.sfl=QLabel('/');B.addWidget(A.sfl);B.addWidget(QLabel('Name:'));A.sfi=QLineEdit(placeholderText='filename.py');A.sfi.returnPressed.connect(A.dosaveas);B.addWidget(A.sfi,1);A.btn(B,'Up',A.sfup);A.btn(B,'Save',A.dosaveas);A.btn(B,'Cancel',A.sb.hide);A.sb.hide();C.addWidget(A.sb);A.ob=QWidget();F=QVBoxLayout(A.ob);F.setContentsMargins(0,0,0,0);F.addWidget(QLabel('Open a Python file:'));A.ol=QListWidget();A.ol.setMaximumHeight(120);A.ol.itemDoubleClicked.connect(A.doopen);F.addWidget(A.ol);G=QHBoxLayout();A.btn(G,'Open',A.doopen);A.btn(G,'Cancel',A.ob.hide);G.addStretch();F.addLayout(G);A.ob.hide();C.addWidget(A.ob);A.mgb=QWidget();H=QHBoxLayout(A.mgb);H.setContentsMargins(0,0,0,0);A.mgl=QLabel();A.mgl.setWordWrap(True);H.addWidget(A.mgl,1);A.myb=A.btn(H,'OK',lambda:A.mclose(True));A.mnb=A.btn(H,'No',lambda:A.mclose(False));A.mgb.hide();A.cnew=False;A.crep=None;C.addWidget(A.mgb)
		for(L,I)in(('F5',A.run),('Ctrl+S',A.save)):J=QAction(A);J.setShortcut(QKeySequence(L));J.triggered.connect(I);A.addAction(J)
	def ask(A,t,y='Yes',n='No'):A.mgl.setText(t);A.myb.setText(y);A.mnb.setText(n);A.mnb.setVisible(n is not None);A.mgb.show()
	def ncode(A):
		if A.ed.toPlainText().strip():A.cnew=True;A.ask('Discard current code?');return
		A.code=None;A.fnl.setText('Untitled.py');A.ed.clear();A.out.clear()
	def chcode(A):
		B=A.vfs.py()
		if not B:A.ask('No Python files in Storage yet. Use Save to create one.',y='OK',n=None);return
		A.ol.clear()
		for C in B:D=QListWidgetItem(C);D.setData(Qt.ItemDataRole.UserRole,C);A.ol.addItem(D)
		A.ol.setCurrentRow(0);A.ob.show()
	def doopen(A):
		B=A.ol.currentItem()
		if B is None:return
		A.ld(B.data(Qt.ItemDataRole.UserRole));A.ob.hide()
	def mclose(A,y):
		A.mgb.hide()
		if A.cnew:
			A.cnew=False
			if y:A.code=None;A.fnl.setText('Untitled.py');A.ed.clear();A.out.clear()
		elif A.crep:
			B,A.crep=A.crep,None
			if y:A.wcode(B);A.sb.hide()
	def ld(A,p):
		B=A.vfs.r(p)
		if B is None:A.ask(f"{p} no longer exists.",y='OK',n=None);return
		A.ed.setPlainText(B.decode('utf-8',errors='replace'));A.code=p;A.folder=posixpath.dirname(p)or'/';A.fnl.setText(posixpath.basename(p));A.stat.setText(f"Opened Storage{p}");A.act(A.st)
	def save(A):
		if A.code:A.wcode(A.code)
		else:A.saveas()
	def saveas(A):A.sfi.setText(posixpath.basename(A.code)if A.code else'untitled.py');A.sfi.selectAll();A.sfl.setText(A.folder);A.sb.show();A.sfi.setFocus()
	def dosaveas(A):
		C=clean(A.sfi.text())
		if not C:return
		if not posixpath.splitext(C)[1]:C+='.py'
		B=A.vfs.join(A.folder,C)
		if A.vfs.isd(B):A.ask('A folder with that name already exists.',y='OK',n=None);return
		if B!=A.code and A.vfs.ex(B):A.crep=B;A.ask(f"{posixpath.basename(B)} already exists. Replace it?");return
		A.wcode(B);A.sb.hide()
	def sfup(A):
		if A.folder!='/':A.folder=posixpath.dirname(A.folder)or'/';A.sfl.setText(A.folder)
	def wcode(A,p):
		try:A.vfs.w(p,A.ed.toPlainText().encode('utf-8'))
		except sqlite3.Error as B:A.ask(str(B),y='OK',n=None);return
		A.code=p;A.folder=posixpath.dirname(p)or'/';A.fnl.setText(posixpath.basename(p));A.stat.setText('Saved');A.flref()
	def run(A):
		D=A.ed.toPlainText()
		if not D.strip():A.out.setPlainText('Nothing to run.');return
		B=None
		try:
			with tempfile.NamedTemporaryFile(mode='w',suffix='.py',encoding='utf-8',delete=False)as E:E.write(D);B=E.name
			C=subprocess.run([sys.executable,B],cwd=tempfile.gettempdir(),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=15,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32'else 0);A.out.setPlainText(C.stdout+C.stderr or'Program finished with no output.');A.stat.setText('Finished'if C.returncode==0 else f"Exit code: {C.returncode}")
		except subprocess.TimeoutExpired:A.out.setPlainText('Stopped: execution exceeded 15 seconds.');A.stat.setText('Timed out')
		except Exception as F:A.out.setPlainText(str(F));A.stat.setText('Error')
		finally:
			if B:
				try:os.remove(B)
				except OSError:0
if __name__=='__main__':app=QApplication(sys.argv);app.setWindowIcon(app_icon());app.setStyleSheet('QMainWindow,QWidget{background:#242424;color:#eeeeee;}QMdiArea#windowWorkspace{background:#0a1a27;border:none;}QMdiSubWindow{border:1px solid #555555;}QWidget#desktop{background:transparent;color:#f2f2f2;}QLabel{color:#eeeeee;}QToolButton#desktopShortcut{color:white;background:transparent;border:1px solid transparent;border-radius:4px;padding:6px;font-size:13px;}QToolButton#desktopShortcut:hover{background:rgba(36,36,36,190);border:1px solid #555555;}QFrame#topbar{background:#202020;border-bottom:1px solid #3b3b3b;}QPushButton#topButton{background:#292929;color:#eeeeee;border:1px solid #414141;padding:4px 9px;border-radius:3px;}QPushButton#topButton:hover{background:#3b3b3b;}QLabel#statusLabel{color:#eeeeee;font-size:11px;background:transparent;}QFrame#taskbar{background:#1b1b1b;border-top:1px solid #3b3b3b;}QPushButton{background:#303030;color:#f0f0f0;border:1px solid #484848;padding:5px 9px;border-radius:3px;}QPushButton:hover{background:#3a3a3a;border-color:#606060;}QPushButton:pressed{background:#1d1d1d;}QToolButton#taskAppButton{background:#262626;border:1px solid #414141;border-radius:4px;padding:3px;}QToolButton#taskAppButton:hover{background:#3b3b3b;border-color:#606060;}QToolButton#taskAppButton:pressed{background:#1d1d1d;}QLineEdit,QPlainTextEdit{background:#181818;color:#eeeeee;border:1px solid #484848;selection-background-color:#555555;}QSplitter::handle{background:#353535;}QScrollBar:vertical,QScrollBar:horizontal{background:#202020;}QMenu{background:#292929;color:#eeeeee;border:1px solid #484848;}QMenu::item:selected{background:#414141;}QToolTip{background:#303030;color:#ffffff;border:1px solid #555555;}QTabWidget#browserTabs::pane{border:1px solid #3b3b3b;background:#181818;}QTabWidget#browserTabs QTabBar::tab{background:#262626;color:#d0d0d0;border:1px solid #3b3b3b;border-bottom:none;padding:6px 10px;min-width:90px;}QTabWidget#browserTabs QTabBar::tab:selected{background:#3a3a3a;color:#ffffff;}QTabWidget#browserTabs QTabBar::tab:hover{background:#333333;}QToolButton#newTabButton{background:#262626;color:#eeeeee;border:1px solid #414141;border-radius:3px;font-weight:bold;}QToolButton#newTabButton:hover{background:#3b3b3b;border-color:#606060;}');window=OS();window.show();sys.exit(app.exec())