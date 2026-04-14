#!/usr/bin/env python3
"""
Launch the SO-ARM ros2_control stack.

Supports both SO100 and SO101 arm variants, selected via the 'model' launch argument.
Starts robot_state_publisher, controller_manager, joint_state_broadcaster,
soarm_controller, and motor diagnostics.

Example usage:
    ros2 launch soarm_control soarm.launch.py
    ros2 launch soarm_control soarm.launch.py model:=so100
    ros2 launch soarm_control soarm.launch.py model:=so101 use_mock:=false serial_port:=/dev/ttyUSB0
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            "model",
            default_value="so101",
            description="Robot model to launch: so100 or so101",
            choices=["so100", "so101"],
        ),
        DeclareLaunchArgument(
            "serial_port",
            default_value="/dev/ttySERVO",
            description="Serial port for STS motor communication",
        ),
        DeclareLaunchArgument(
            "use_mock",
            default_value="true",
            description="Use mock/simulation mode (no hardware required)",
        ),
        DeclareLaunchArgument(
            "use_sync_write",
            default_value="true",
            description="Enable SyncWrite for coordinated multi-motor commands",
        ),
    ]

    model = LaunchConfiguration("model")
    serial_port = LaunchConfiguration("serial_port")
    use_mock = LaunchConfiguration("use_mock")
    use_sync_write = LaunchConfiguration("use_sync_write")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("soarm_description"),
                    "urdf",
                    model,
                    [model, ".urdf.xacro"],
                ]
            ),
            " ",
            "serial_port:=",
            serial_port,
            " ",
            "use_mock:=",
            use_mock,
            " ",
            "use_sync_write:=",
            use_sync_write,
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    controller_config = PathJoinSubstitution(
        [FindPackageShare("soarm_control"), "config", [model, "_controllers.yaml"]]
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="log",
        parameters=[robot_description],
        name="robot_state_publisher",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", "WARN"],
    )

    controller_manager_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, controller_config],
        output="log",
        emulate_tty=True,
        name="controller_manager",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        output="both",
    )

    soarm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["soarm_controller", "-c", "/controller_manager"],
        output="both",
    )

    diagnostics_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("sts_hardware_interface"),
                        "launch",
                        "motor_diagnostics.launch.py",
                    ]
                )
            ]
        )
    )

    return LaunchDescription(
        [
            *declared_arguments,
            robot_state_publisher_node,
            controller_manager_node,
            TimerAction(period=2.0, actions=[joint_state_broadcaster_spawner]),
            TimerAction(period=2.5, actions=[soarm_controller_spawner]),
            TimerAction(period=3.0, actions=[diagnostics_launch]),
        ]
    )
