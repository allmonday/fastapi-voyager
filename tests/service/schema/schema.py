"""
示例实体定义 - 用于 GraphQL 和 REST API 演示
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic_resolve import (
    Relationship,
    base_entity,
    mutation,
    query,
)
from pydantic_resolve.utils.dataloader import build_list, build_object

from .base_entity import BaseEntity

# =====================================
# Input Types for Mutations
# =====================================


class CreateMemberInput(BaseModel):
    """创建成员的输入类型"""

    first_name: str = Field(description="名")
    last_name: str = Field(description="姓")


class UpdateMemberInput(BaseModel):
    """更新成员的输入类型"""

    first_name: Optional[str] = Field(default=None, description="名")
    last_name: Optional[str] = Field(default=None, description="姓")


class CreateTaskInput(BaseModel):
    """创建任务的输入类型"""

    story_id: int = Field(description="所属 Story ID")
    description: str = Field(description="任务描述")
    owner_id: int = Field(description="负责人 ID")


class UpdateTaskInput(BaseModel):
    """更新任务的输入类型"""

    story_id: Optional[int] = Field(default=None, description="所属 Story ID")
    description: Optional[str] = Field(default=None, description="任务描述")
    owner_id: Optional[int] = Field(default=None, description="负责人 ID")


class CreateStoryInput(BaseModel):
    """创建 Story 的输入类型"""

    type: Literal["feature", "bugfix"] = Field(description="类型")
    sprint_id: int = Field(description="所属 Sprint ID")
    title: str = Field(description="标题")
    description: str = Field(description="描述")
    dct: dict = Field(default_factory=dict, description="额外信息")


class UpdateStoryInput(BaseModel):
    """更新 Story 的输入类型"""

    type: Optional[Literal["feature", "bugfix"]] = Field(
        default=None, description="类型"
    )
    sprint_id: Optional[int] = Field(default=None, description="所属 Sprint ID")
    title: Optional[str] = Field(default=None, description="标题")
    description: Optional[str] = Field(default=None, description="描述")


class CreateSprintInput(BaseModel):
    """创建 Sprint 的输入类型"""

    name: str = Field(description="Sprint 名称")


class UpdateSprintInput(BaseModel):
    """更新 Sprint 的输入类型"""

    name: Optional[str] = Field(default=None, description="Sprint 名称")


# =====================================
# 模拟数据库（先声明，在文件末尾初始化）
# =====================================

members_db: Dict[int, "Member"] = {}
tasks_db: Dict[int, "Task"] = {}
stories_db: Dict[int, "Story"] = {}
sprints_db: Dict[int, "Sprint"] = {}

member_id_counter = 0
task_id_counter = 0
story_id_counter = 0
sprint_id_counter = 0


# =====================================
# DataLoader 函数
# =====================================


async def member_loader(member_ids: List[int]) -> List[dict]:
    """成员批量加载器"""
    members = [m if m else None for m in [members_db.get(mid) for mid in member_ids]]
    return list(build_object(members, member_ids, lambda m: m.id if m else None))


async def task_loader(task_ids: List[int]) -> List[dict]:
    """任务批量加载器"""
    tasks = [t if t else None for t in [tasks_db.get(tid) for tid in task_ids]]
    return list(build_object(tasks, task_ids, lambda t: t.id if t else None))


async def story_loader(story_ids: List[int]) -> List[dict]:
    """Story 批量加载器"""
    stories = [s if s else None for s in [stories_db.get(sid) for sid in story_ids]]
    return list(build_object(stories, story_ids, lambda s: s.id if s else None))


async def sprint_loader(sprint_ids: List[int]) -> List[dict]:
    """Sprint 批量加载器"""
    sprints = [sp if sp else None for sp in [sprints_db.get(sid) for sid in sprint_ids]]
    return list(build_object(sprints, sprint_ids, lambda sp: sp.id if sp else None))


async def story_to_tasks_loader(story_ids: List[int]) -> List[List[dict]]:
    """根据 Story ID 加载关联的 Tasks"""
    all_tasks = list(tasks_db.values())
    return list(build_list(all_tasks, story_ids, lambda t: t.story_id))


async def sprint_to_stories_loader(sprint_ids: List[int]) -> List[List[dict]]:
    """根据 Sprint ID 加载关联的 Stories"""
    all_stories = list(stories_db.values())
    return list(build_list(all_stories, sprint_ids, lambda s: s.sprint_id))


# =====================================
# 实体定义
# =====================================


class Member(BaseModel, BaseEntity):
    """成员实体"""

    __relationships__ = []

    id: int = Field(description="成员唯一标识 ID")
    first_name: str = Field(description="名")
    last_name: str = Field(description="姓")

    @query
    async def get_all(cls, limit: int = 10, offset: int = 0) -> List["Member"]:
        """获取所有成员（分页）"""
        all_members = list(members_db.values())
        return all_members[offset : offset + limit]

    @query
    async def get_by_id(cls, id: int) -> Optional["Member"]:
        """根据 ID 获取成员"""
        return members_db.get(id)

    @mutation
    async def create_member(cls, first_name: str, last_name: str) -> "Member":
        """创建新成员"""
        global member_id_counter
        member_id_counter += 1
        new_member = Member(
            id=member_id_counter, first_name=first_name, last_name=last_name
        )
        members_db[member_id_counter] = new_member
        return new_member

    @mutation
    async def create_member_with_input(cls, input: CreateMemberInput) -> "Member":
        """使用 Input Type 创建新成员"""
        global member_id_counter
        member_id_counter += 1
        new_member = Member(
            id=member_id_counter,
            first_name=input.first_name,
            last_name=input.last_name,
        )
        members_db[member_id_counter] = new_member
        return new_member

    @mutation
    async def update_member(
        cls, id: int, first_name: Optional[str] = None, last_name: Optional[str] = None
    ) -> Optional["Member"]:
        """更新成员信息"""
        if id in members_db:
            member = members_db[id]
            if first_name is not None:
                member.first_name = first_name
            if last_name is not None:
                member.last_name = last_name
            return member
        return None

    @mutation
    async def update_member_with_input(
        cls, id: int, input: UpdateMemberInput
    ) -> Optional["Member"]:
        """使用 Input Type 更新成员信息"""
        if id in members_db:
            member = members_db[id]
            if input.first_name is not None:
                member.first_name = input.first_name
            if input.last_name is not None:
                member.last_name = input.last_name
            return member
        return None

    @mutation
    async def delete_member(cls, id: int) -> bool:
        """删除成员，返回是否成功"""
        if id in members_db:
            del members_db[id]
            return True
        return False


class Task(BaseModel, BaseEntity):
    """任务实体"""

    __relationships__ = [
        Relationship(
            fk="owner_id",
            target=Member,
            loader=member_loader,
            name="owner",
        ),
        Relationship(
            fk="story_id",
            target="Story",
            loader=story_loader,
            name="story",
        ),
    ]
    id: int = Field(description="The unique identifier of the task")
    story_id: int = Field(description="所属 Story ID")
    description: str = Field(description="任务描述")
    owner_id: int = Field(description="负责人 ID")

    @query
    async def get_all(cls, limit: int = 10, offset: int = 0) -> List["Task"]:
        """获取所有任务（分页）"""
        all_tasks = list(tasks_db.values())
        return all_tasks[offset : offset + limit]

    @query
    async def get_by_id(cls, id: int) -> Optional["Task"]:
        """根据 ID 获取任务"""
        return tasks_db.get(id)

    @query
    async def get_by_story_id(cls, story_id: int) -> List["Task"]:
        """根据 Story ID 获取任务列表"""
        return [t for t in tasks_db.values() if t.story_id == story_id]

    @mutation
    async def create_task(cls, story_id: int, description: str, owner_id: int) -> "Task":
        """创建新任务"""
        global task_id_counter
        task_id_counter += 1
        new_task = Task(
            id=task_id_counter,
            story_id=story_id,
            description=description,
            owner_id=owner_id,
        )
        tasks_db[task_id_counter] = new_task
        return new_task

    @mutation
    async def create_task_with_input(cls, input: CreateTaskInput) -> "Task":
        """使用 Input Type 创建新任务"""
        global task_id_counter
        task_id_counter += 1
        new_task = Task(
            id=task_id_counter,
            story_id=input.story_id,
            description=input.description,
            owner_id=input.owner_id,
        )
        tasks_db[task_id_counter] = new_task
        return new_task

    @mutation
    async def update_task(
        cls,
        id: int,
        story_id: Optional[int] = None,
        description: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> Optional["Task"]:
        """更新任务信息"""
        if id in tasks_db:
            task = tasks_db[id]
            if story_id is not None:
                task.story_id = story_id
            if description is not None:
                task.description = description
            if owner_id is not None:
                task.owner_id = owner_id
            return task
        return None

    @mutation
    async def update_task_with_input(
        cls, id: int, input: UpdateTaskInput
    ) -> Optional["Task"]:
        """使用 Input Type 更新任务信息"""
        if id in tasks_db:
            task = tasks_db[id]
            if input.story_id is not None:
                task.story_id = input.story_id
            if input.description is not None:
                task.description = input.description
            if input.owner_id is not None:
                task.owner_id = input.owner_id
            return task
        return None

    @mutation
    async def delete_task(cls, id: int) -> bool:
        """删除任务，返回是否成功"""
        if id in tasks_db:
            del tasks_db[id]
            return True
        return False


class Story(BaseModel, BaseEntity):
    """Story 实体"""

    __relationships__ = [
        Relationship(
            fk="id",
            target=list["Task"],
            loader=story_to_tasks_loader,
            name="tasks",
        ),
    ]
    id: int = Field(description="Story ID")
    type: Literal["feature", "bugfix"] = Field(description="类型")
    dct: dict = Field(default_factory=dict, description="额外信息")
    sprint_id: int = Field(description="所属 Sprint ID")
    title: str = Field(description="标题")
    description: str = Field(description="描述")

    @query
    async def get_all(
        cls, limit: int = 10, offset: int = 0, sprint_id: Optional[int] = None
    ) -> List["Story"]:
        """获取所有 Story（分页，可按 Sprint 筛选）"""
        all_stories = list(stories_db.values())
        if sprint_id:
            all_stories = [s for s in all_stories if s.sprint_id == sprint_id]
        return all_stories[offset : offset + limit]

    @query
    async def get_by_id(cls, id: int) -> Optional["Story"]:
        """根据 ID 获取 Story"""
        return stories_db.get(id)

    @query
    async def get_by_sprint_id(cls, sprint_id: int) -> List["Story"]:
        """根据 Sprint ID 获取 Story 列表"""
        return [s for s in stories_db.values() if s.sprint_id == sprint_id]

    @mutation
    async def create_story(
        cls,
        type: Literal["feature", "bugfix"],
        sprint_id: int,
        title: str,
        description: str,
        dct: dict = None,
    ) -> "Story":
        """创建新 Story"""
        global story_id_counter
        story_id_counter += 1
        new_story = Story(
            id=story_id_counter,
            type=type,
            sprint_id=sprint_id,
            title=title,
            description=description,
            dct=dct or {},
        )
        stories_db[story_id_counter] = new_story
        return new_story

    @mutation
    async def create_story_with_input(cls, input: CreateStoryInput) -> "Story":
        """使用 Input Type 创建新 Story"""
        global story_id_counter
        story_id_counter += 1
        new_story = Story(
            id=story_id_counter,
            type=input.type,
            sprint_id=input.sprint_id,
            title=input.title,
            description=input.description,
            dct=input.dct,
        )
        stories_db[story_id_counter] = new_story
        return new_story

    @mutation
    async def update_story(
        cls,
        id: int,
        type: Optional[Literal["feature", "bugfix"]] = None,
        sprint_id: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional["Story"]:
        """更新 Story 信息"""
        if id in stories_db:
            story = stories_db[id]
            if type is not None:
                story.type = type
            if sprint_id is not None:
                story.sprint_id = sprint_id
            if title is not None:
                story.title = title
            if description is not None:
                story.description = description
            return story
        return None

    @mutation
    async def update_story_with_input(
        cls, id: int, input: UpdateStoryInput
    ) -> Optional["Story"]:
        """使用 Input Type 更新 Story 信息"""
        if id in stories_db:
            story = stories_db[id]
            if input.type is not None:
                story.type = input.type
            if input.sprint_id is not None:
                story.sprint_id = input.sprint_id
            if input.title is not None:
                story.title = input.title
            if input.description is not None:
                story.description = input.description
            return story
        return None

    @mutation
    async def delete_story(cls, id: int) -> bool:
        """删除 Story，返回是否成功"""
        if id in stories_db:
            del stories_db[id]
            return True
        return False


class Sprint(BaseModel, BaseEntity):
    """Sprint 实体"""

    __relationships__ = [
        Relationship(
            fk="id",
            target=list["Story"],
            loader=sprint_to_stories_loader,
            name="stories",
        ),
        Relationship(
            fk="id",
            target=list["Story"],
            loader=sprint_to_stories_loader,
            name="done_stories",
        ),
    ]
    id: int = Field(description="Sprint ID")
    name: str = Field(description="Sprint 名称")

    @query
    async def get_all(cls, limit: int = 10, offset: int = 0) -> List["Sprint"]:
        """获取所有 Sprint（分页）"""
        all_sprints = list(sprints_db.values())
        return all_sprints[offset : offset + limit]

    @query
    async def get_by_id(cls, id: int) -> Optional["Sprint"]:
        """根据 ID 获取 Sprint"""
        return sprints_db.get(id)

    @mutation
    async def create_sprint(cls, name: str) -> "Sprint":
        """创建新 Sprint"""
        global sprint_id_counter
        sprint_id_counter += 1
        new_sprint = Sprint(id=sprint_id_counter, name=name)
        sprints_db[sprint_id_counter] = new_sprint
        return new_sprint

    @mutation
    async def create_sprint_with_input(cls, input: CreateSprintInput) -> "Sprint":
        """使用 Input Type 创建新 Sprint"""
        global sprint_id_counter
        sprint_id_counter += 1
        new_sprint = Sprint(id=sprint_id_counter, name=input.name)
        sprints_db[sprint_id_counter] = new_sprint
        return new_sprint

    @mutation
    async def update_sprint(
        cls, id: int, name: Optional[str] = None
    ) -> Optional["Sprint"]:
        """更新 Sprint 信息"""
        if id in sprints_db:
            sprint = sprints_db[id]
            if name is not None:
                sprint.name = name
            return sprint
        return None

    @mutation
    async def update_sprint_with_input(
        cls, id: int, input: UpdateSprintInput
    ) -> Optional["Sprint"]:
        """使用 Input Type 更新 Sprint 信息"""
        if id in sprints_db:
            sprint = sprints_db[id]
            if input.name is not None:
                sprint.name = input.name
            return sprint
        return None

    @mutation
    async def delete_sprint(cls, id: int) -> bool:
        """删除 Sprint，返回是否成功"""
        if id in sprints_db:
            del sprints_db[id]
            return True
        return False


# =====================================
# 初始化模拟数据库
# =====================================


def init_db():
    """初始化模拟数据库"""
    global members_db, tasks_db, stories_db, sprints_db
    global member_id_counter, task_id_counter, story_id_counter, sprint_id_counter

    member_id_counter = 2
    task_id_counter = 4
    story_id_counter = 2
    sprint_id_counter = 1

    members_db.clear()
    tasks_db.clear()
    stories_db.clear()
    sprints_db.clear()

    members_db.update(
        {
            1: Member(id=1, first_name="John", last_name="Doe"),
            2: Member(id=2, first_name="Jane", last_name="Smith"),
        }
    )

    sprints_db.update({1: Sprint(id=1, name="Sprint 1")})

    stories_db.update(
        {
            1: Story(
                id=1,
                type="feature",
                dct={"key": "value"},
                sprint_id=1,
                title="First Story",
                description="This is the first story",
            ),
            2: Story(
                id=2,
                type="bugfix",
                dct={},
                sprint_id=1,
                title="Second Story",
                description="This is the second story",
            ),
        }
    )

    tasks_db.update(
        {
            1: Task(id=1, story_id=1, description="Task 1 for Story 1", owner_id=1),
            2: Task(id=2, story_id=1, description="Task 2 for Story 1", owner_id=2),
            3: Task(id=3, story_id=2, description="Task 1 for Story 2", owner_id=1),
            4: Task(id=4, story_id=2, description="Task 2 for Story 2", owner_id=2),
        }
    )


# 自动初始化
init_db()
