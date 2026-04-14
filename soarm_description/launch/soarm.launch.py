#!/usr/bin/env python3
"""
Launch the SO-ARM robot description.

Supports both SO100 and SO101 arm variants, selected via the 'model' launch argument.
Starts robot_state_publisher and optionally joint_state_publisher_gui for manual
joint control in mock/visualization mode.

Example usage:
    ros2 launch soarm_description soarm.launch.py
    ros2 launch soarm_description soarm.launch.py model:=so100
    ros2 launch soarm_description soarm.launch.py model:=so101 use_mock:=true gui:=true
    ros2 launch soarm_description soarm.launch.py serial_port:=/dev/ttyACM0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
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
    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "model",
            default_value="so101",
            description="Robot model to launch: so100 or so101",
            choices=["so100", "so101"],
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "serial_port",
            default_value="/dev/ttySERVO",
            description="Serial port for STS motor communication",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_mock",
            default_value="false",
            description="Use mock/simulation mode (no hardware required)",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sync_write",
            default_value="true",
            description="Enable SyncWrite for coordinated multi-motor commands",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="false",
            description="Start joint_state_publisher_gui for manual joint control",
        )
    )

    model = LaunchConfiguration("model")
    serial_port = LaunchConfiguration("serial_port")
    use_mock = LaunchConfiguration("use_mock")
    use_sync_write = LaunchConfiguration("use_sync_write")
    gui = LaunchConfiguration("gui")

    # Build URDF path: urdf/{model}/{model}.urdf.xacro
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

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="log",
        parameters=[robot_description],
        name="robot_state_publisher",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", "WARN"],
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        output="log",
        condition=IfCondition(gui),
    )

    return LaunchDescription(
        [
            *declared_arguments,
            robot_state_publisher_node,
            joint_state_publisher_gui_node,
        ]
    )
