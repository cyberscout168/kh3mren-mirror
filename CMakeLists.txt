cmake_minimum_required(VERSION 3.21)

project(ScreenMirror VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 6.4 REQUIRED COMPONENTS Core Gui Widgets)

qt_add_executable(ScreenMirror
    src/main.cpp
    src/adbmanager.cpp
    src/adbmanager.h
    src/mainwindow.cpp
    src/mainwindow.h
)

target_link_libraries(ScreenMirror PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets)

if(WIN32)
    set_target_properties(ScreenMirror PROPERTIES WIN32_EXECUTABLE TRUE)
elseif(APPLE)
    set_target_properties(ScreenMirror PROPERTIES MACOSX_BUNDLE TRUE)
endif()

include(GNUInstallDirs)
install(TARGETS ScreenMirror
    BUNDLE DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
