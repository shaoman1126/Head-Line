from datetime import datetime  # 就是这个！
from fastapi import FastAPI, Path, Query, HTTPException, Depends
from pydantic import BaseModel, Field  # 必须加这一行！
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy import DateTime, func, String, Float, Integer, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

app = FastAPI()

#
@app.middleware("http")
async def middleware2(request, call_next):
    print('中间件2开始')
    response = await call_next(request)
    print('中间件2结束')
    return response


# 中间件
@app.middleware("http")
async def middleware1(request, call_next):
    print('中间件1开始')
    response = await call_next(request)
    print('中间件1结束')
    return response


@app.get("/")
async def root():
    return {"message": "Hello World1"}


# 访问 /hello   响应结构 msg: 你好 FastAPI
@app.get('/hello')
async def get_hello():
    return {"msg": "你好 FastAPI"}


# 访问路径/user/hello。响应结果是 {"msg":"我正在学习FastAPI ...."}
@app.get('/user/hello')
async def get_user():
    return {"msg": "我正在学习FastAPI ...."}


@app.get('/book/{id}')
async def get_book(id: int = Path(..., gt=0, lt=101, description='书籍id: 取值范围1-100')):
    return {"用户ID": f"{id}", "名称": f"普通用户{id}"}


# 需求：查找书籍的作者，路径参赛 name,长度范围 2-10
@app.get('/find_book/{name}')
async def find_book(name: str = Path(..., min_length=2, max_length=10, description='查找作者名字')):
    return {"msg": f"作者的名字叫：{name}"}


# 接口： 以新闻分类 id 为参数设计URL,id 范围为 1～100
@app.get('/new/class_id/{ids}')
async def new_class(ids: int = Path(..., gt=0, lt=101, description='新闻分类ID 1-100')):
    return {"msg": f"新闻分类{ids}"}


# 接口：以新闻分类名称为参数设计URL,分类名称长度 2～ 10
@app.get('/new/class_name/{name}')
async def new_class(name: str = Path(..., min_length=2, max_length=10, description='新闻分类名称')):
    return {"msg": f"新闻分类名称：{name}"}


# 查询新闻 -> 分页， skip:跳过的记录数 limit :返回的记录数 10
@app.get('/news/news_list')
async def get_news_list(
        skip: int = Query(0, description='跳过的记录数', lt=101),
        limit: int = Query(10, description='返回的记录数')
):
    return {"skip": skip, "limit": limit}


# 需求：设计接口查询图书，要求携带两个查询参数：图书分类和价格
@app.get('/find_book/book_list')
async def get_book_list(
        book_class: str = Query('弗勒尔佐德之心', min_length=5, max_length=255),
        price: int = Query(50, gt=49, lt=101)
):
    return {"class": f"图书分类{book_class}", "price": f"{price}"}


# 注册：用户名和密码 -> str
class User(BaseModel):
    username: str = Field(default='寒冰射手', min_length=2, max_length=10, description='用户名长度2-10个字')
    password: str = Field(min_length=3, max_length=20)


@app.post('/login')
async def login(user: User):
    return user


class Book(BaseModel):
    name: str = Field(..., min_length=2, max_length=20)
    author: str = Field(min_length=2, max_length=10)
    publisher: str = Field(default='黑马出版社')
    price: int = Field(..., gt=0)


@app.post('/add/book')
async def add_book(info: Book):
    return info


# 接口 -> 响应 HTML 代码
@app.get('/html', response_class=HTMLResponse)
async def get_html():
    return '<h1>这是一级标题</h1>'


# 接口 -> 返回一张图
@app.get('/file')
async def get_file():
    path = 'files/1-1.png'
    return FileResponse(path)


# 需求: 新闻接口 -> 响应数据格式 id,title,content

class News(BaseModel):
    id: int
    title: str
    content: str


@app.get('/v2/news/{id}', response_model=News)
async def v2_news(id: int):
    return {
        "id": f"{id}",
        "title": f"这是第{id}本书",
        "content": f"这是一本{id} 内容"
    }


# 需求：按 id查询新闻 1 -> 6
@app.get('/v2/find_book/{id}')
async def get_book(id: int):
    list = [1, 3, 4, 5, 7]
    if id not in list:
        raise HTTPException(status_code=404, detail='你查询的新闻不存在')
    return {"id": f"{id}"}


# 分页参数逻辑共用：新闻列表和用户列表
# 1.依赖项
async def common_parameters(
        skip: int = Query(0, gt=0),
        limit: int = Query(10, lt=60)):
    return {"skip": skip, "limit": limit}


@app.get('/v3/news_list')
async def get__fni_news_list(common=Depends(common_parameters)):
    return common


# 1.创建异步引擎
ASYNC_DATABASE_URL = "mysql+aiomysql://root@localhost:3306/FaskAPI_db?charset=utf8mb4"
# ASYNC_DATABASE_URL = "mysql+asyncmy://root@localhost:3306/test?charset=utf8mb4"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # 可选，输出 SQL 日志
    pool_size=10,  # 连接池
    max_overflow=20,  # 允许额外的连接数
)


# 定义模型类： 基类 + 表对应的模型类
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), default=func.now(),
                                                  comment='创建时间')
    update_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), default=func.now(),
                                                  onupdate=func.now(),
                                                  comment="修改时间")


class Book(Base):
    __tablename__ = 'book'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="书籍ID")
    bookname: Mapped[str] = mapped_column(String(255), comment="数名")
    author: Mapped[str] = mapped_column(String(255), comment="作者")
    price: Mapped[float] = mapped_column(Float, comment="价格")
    publisher: Mapped[str] = mapped_column(String(255), comment="出版社")


class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(255), comment="用户名")
    password: Mapped[str] = mapped_column(String(255), comment="密码")
    sex: Mapped[str] = mapped_column(String(255), comment="性别")


# 3. 建表
async def create_table():
    # 获取数据库的异步引擎，创建食物 --建表
    async with async_engine.begin() as conn:
        await  conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def startup_event():
    await create_table()


# 新版 FastAPI 生命周期（替代旧的 on_event）
# async def lifespan(app: FastAPI):
#     # 启动时执行（建表）
#     await create_table()
#     print("✅ 项目启动完成，数据库表已创建")
#     yield
#     # 关闭时执行（可选）
#     print("✅ 项目关闭")


# 需求： 查询功能的接口，查询图书 -> 依赖注入：创建依赖项获取数据库会话 + Depends 注入路由处理函数
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,  # 绑定数据库引擎
    class_=AsyncSession,  # 制定绘画类
    expire_on_commit=False,  # 提交后回话不过期，不会重启查询数据库
)


# 依赖项
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 返回数据库会话路由处理函数
            await session.commit()  # 提交事物
        except Exception:
            await session.rollback()  # 有异常,回滚
            raise
        finally:
            await session.close()  # 关闭会话


@app.get("/book/books/ss")
async def get_books_list(db: AsyncSession = Depends(get_database)):
    # 查询
    result = await db.execute(select(Book))
    # book = result.scalars().all()
    # book = result.scalars().first()
    book = await db.get(Book, 1)
    return book
    return {"books": "books"}


# 需求： 路径参数，书籍ID
@app.get("/book/get_book/{book_id}")
async def get_book(book_id: int, db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    books = result.scalar_one_or_none()
    return books


# 需求： 条件 价格大于等于200
@app.get("/book/search_book/find")
async def search_book(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where(Book.price >= 50000))
    books = result.scalars().all()
    return books


# 需求： 作者 曹 % _
@app.get("/v22/book/search_book/find")
async def search_sbook(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where(Book.author.like('曹')))
    books = result.scalars().all()
    return books


# 需求： 作者 曹 % _
@app.get("/v22/book/search_book/asdasd")
async def search_sbook(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where(Book.author.like('曹_')))
    books = result.scalars().all()
    return books


# 需求： 作者 曹  并且 价格
@app.get("/v23/book/search_book/asdasd")
async def search_sbook(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where((Book.author.like('曹_')) & (Book.price > 5000)))
    books = result.scalars().all()
    return books


# 需求： 作者 曹  并且 价格
@app.get("/v223/book/search_book/asdasd")
async def search_sbook(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where((Book.author.like('曹_')) | (Book.price > 5000)))
    books = result.scalars().all()
    return books


# 需求：数据 id 列表，数据库里面的 id 如果在 书籍id 列表里面 就返回
@app.get("/v24/book/search_book/asdasd")
async def search_sbook(db: AsyncSession = Depends(get_database)):
    id_list = [10, 2, 3]
    result = await  db.execute(select(Book).where(Book.id.in_(id_list)))
    book = result.scalars().all()
    return book


# 需求：数据 id 列表，数据库里面的 id 如果在 书籍id 列表里面 就返回
@app.get("/23/book/func")
async def search_sbook_func(db: AsyncSession = Depends(get_database)):
    # result = await db.execute(select(func.count(Book.id)))
    # result = await db.execute(select(func.avg(Book.id)))
    # result = await db.execute(select(func.sum(Book.price)))
    result = await db.execute(select(func.max(Book.price)))
    count = result.scalar()  # 用来提取一个数值 + 标量值
    return count


# 需求 ：分页

@app.get("/24/book/ix")
async def search_sbook_ix(
        page: int = 1,
        page_size: int = 1,
        db: AsyncSession = Depends(get_database)):
    skip = (page - 1) * page_size
    stmt = select(Book).offset(skip).limit(page_size)
    result = await db.execute(stmt)
    books = result.scalars().all()
    return books


# 需求新增

class BookBase(BaseModel):
    bookname: str
    author: str
    price: int
    publisher: str


@app.post("/v26/book/add")
async def add_book(book: BookBase, db: AsyncSession = Depends(get_database)):
    book_obj = Book(**book.__dict__)
    db.add(book_obj)
    await db.commit()
    return book


# 修改
class BookUpdate(BaseModel):
    bookname: str
    author: str
    price: int
    publisher: str


@app.put('/27/book/update/{book_id}')
async def update_book(
        book_id: int,
        data: BookUpdate,
        db: AsyncSession = Depends(get_database)
):
    # 查找图书
    db_book = await db.get(Book, book_id)

    # 如果未找到
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # 查询赋值
    db_book.bookname = data.bookname
    db_book.author = data.author
    db_book.price = data.price
    db_book.publisher = data.publisher

    await db.commit()
    return db_book


# 删除
@app.delete('/27/book/delete/{book_id}')
async def delete_book(book_id: int, db: AsyncSession = Depends(get_database)):
    db_book = await db.get(Book, book_id)
    print(f"查询的到吗{db_book}")
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(db_book)
    await db.commit()
    return {"msg": "删除成功"}
