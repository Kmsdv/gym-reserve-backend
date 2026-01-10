# *社区健身设施预约与推荐系统* 数据库课程设计代码 

## 后端环境配置

在编译器中打开 `houduan` 文件夹

数据库相关配置在 `config.py` 文件中

后端操作相关Python代码在 `app.py` 文件中



### 修改数据库相关设置

打开`Navicat Premium`, 右键连接 - 新建数据库

右键新建的数据库 - 运行SQL文件 - 选择`sjk.sql`

修改`config.py`文件中相关配置, 与你的数据库对应

启动数据库  右键新建的数据库 - 打开数据库

### 修改Python环境相关设置

在终端中创建后端 conda 虚拟环境

```bash
conda create -n web python=3.12
```

激活环境

```bash
conda activate web
```

安装相关依赖包

```bash
 pip install -r requirements.txt
```

运行 `app.py` 文件

```bash
python app.py
```



## 前端环境配置

在编译器中打开 `qianduan` 文件夹

运行项目 在终端中输入

```bash
npm run dev
```



然后项目就能运行了🎉🎉