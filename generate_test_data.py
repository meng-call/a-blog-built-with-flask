# generate_test_data.py - 生成中文测试数据

from app import create_app, db
from app.models import User, Role, Post, Comment
from faker import Faker
import random

# 创建 Flask 应用
app = create_app('development')

# 初始化 Faker，设置中文
fake = Faker('zh_CN')


def generate_users(count=10):
    """生成随机用户"""
    print(f"正在生成 {count} 个用户...")

    users = []
    for i in range(count):
        email = fake.email()
        username = fake.user_name()

        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            continue

        user = User(
            email=email,
            username=username,
            password='password123',  # 统一密码
            confirmed=True,
            name=fake.name(),
            location=fake.city(),
            about_me=fake.text(max_nb_chars=200),
            member_since=fake.date_time_between(start_date='-2y', end_date='now')
        )

        db.session.add(user)
        users.append(user)

        if (i + 1) % 5 == 0:
            print(f"  已生成 {i + 1} 个用户")

    try:
        db.session.commit()
        print(f"成功生成 {len(users)} 个用户")
        return users
    except Exception as e:
        db.session.rollback()
        print(f"生成用户失败: {e}")
        return []


def generate_posts(count=50, users=None):
    """生成随机文章"""
    if not users:
        users = User.query.all()

    if not users:
        print("没有用户，无法生成文章")
        return []

    print(f"正在生成 {count} 篇文章...")

    posts = []
    for i in range(count):
        # 随机选择一个作者
        author = random.choice(users)

        post = Post(
            body=fake.text(max_nb_chars=500),
            timestamp=fake.date_time_between(start_date='-6m', end_date='now'),
            author=author
        )

        db.session.add(post)
        posts.append(post)

        if (i + 1) % 10 == 0:
            print(f"  已生成 {i + 1} 篇文章")

    try:
        db.session.commit()
        print(f"成功生成 {len(posts)} 篇文章")
        return posts
    except Exception as e:
        db.session.rollback()
        print(f"生成文章失败: {e}")
        return []


def generate_comments(count=100, users=None, posts=None):
    """生成随机评论"""
    if not users:
        users = User.query.all()
    if not posts:
        posts = Post.query.all()

    if not users or not posts:
        print("没有用户或文章，无法生成评论")
        return []

    print(f"正在生成 {count} 条评论...")

    comments = []
    for i in range(count):
        # 随机选择作者和文章
        author = random.choice(users)
        post = random.choice(posts)

        comment = Comment(
            body=fake.text(max_nb_chars=200),
            timestamp=fake.date_time_between(start_date='-3m', end_date='now'),
            author=author,
            post=post
        )

        db.session.add(comment)
        comments.append(comment)

        if (i + 1) % 20 == 0:
            print(f"  已生成 {i + 1} 条评论")

    try:
        db.session.commit()
        print(f"成功生成 {len(comments)} 条评论")
        return comments
    except Exception as e:
        db.session.rollback()
        print(f"生成评论失败: {e}")
        return []


def generate_follows(users=None):
    """生成随机关注关系"""
    if not users:
        users = User.query.all()

    if len(users) < 2:
        print("用户数量不足，无法生成关注关系")
        return

    print("正在生成关注关系...")

    follow_count = 0
    for user in users:
        # 每个用户随机关注 0-5 个其他用户
        follow_targets = random.sample(
            [u for u in users if u != user],
            min(random.randint(0, 5), len(users) - 1)
        )

        for target in follow_targets:
            if not user.is_following(target):
                user.follow(target)
                follow_count += 1

    try:
        db.session.commit()
        print(f"成功生成 {follow_count} 个关注关系")
    except Exception as e:
        db.session.rollback()
        print(f"生成关注关系失败: {e}")


def clear_data():
    """清空所有测试数据"""
    print("清空现有数据...")

    # 按依赖顺序删除
    Comment.query.delete()
    Post.query.delete()

    # 删除关注关系
    from app.models import Follow
    Follow.query.delete()

    # 删除用户（保留管理员）
    admin_role = Role.query.filter_by(name='Administrator').first()
    if admin_role:
        admin_users = User.query.filter_by(role=admin_role).all()
        admin_emails = [u.email for u in admin_users]

        User.query.filter(~User.email.in_(admin_emails)).delete()
    else:
        User.query.delete()

    db.session.commit()
    print("数据已清空")


def main():
    """主函数"""
    with app.app_context():
        print("=" * 50)
        print("  Flask 中文测试数据生成器")
        print("=" * 50)
        print()

        # 确保角色存在
        print("1. 初始化角色...")
        Role.insert_roles()
        print("   角色初始化完成")
        print()

        # 询问是否清空数据
        choice = input("是否清空现有测试数据？(y/n): ")
        if choice.lower() == 'y':
            clear_data()
            print()

        # 生成用户
        print("2. 生成用户...")
        user_count = int(input("   请输入用户数量 (默认10): ") or "10")
        users = generate_users(user_count)
        print()

        # 生成文章
        print("3. 生成文章...")
        post_count = int(input("   请输入文章数量 (默认50): ") or "50")
        posts = generate_posts(post_count, users)
        print()

        # 生成评论
        print("4. 生成评论...")
        comment_count = int(input("   请输入评论数量 (默认100): ") or "100")
        comments = generate_comments(comment_count, users, posts)
        print()

        # 生成关注关系
        print("5. 生成关注关系...")
        generate_follows(users)
        print()

        # 统计信息
        print("=" * 50)
        print("  生成完成！统计信息：")
        print("=" * 50)
        print(f"  用户数: {User.query.count()}")
        print(f"  文章数: {Post.query.count()}")
        print(f"  评论数: {Comment.query.count()}")

        from app.models import Follow
        print(f"  关注关系数: {Follow.query.count()}")
        print()
        print("  所有用户的统一密码: password123")
        print("=" * 50)


if __name__ == '__main__':
    main()
