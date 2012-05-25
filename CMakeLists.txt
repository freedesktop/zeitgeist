cmake_minimum_required(VERSION 2.8)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/")
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/vala/vala/")

set(ZEITGEIST_VERSION "0.9.1")

find_package(Vala REQUIRED)
include(${VALA_USE_FILE})

find_package(GLIB2 REQUIRED)
find_package(GObject REQUIRED)
find_package(Sqlite REQUIRED)
find_package(PkgConfig REQUIRED)

pkg_search_module(GIO REQUIRED gio-unix-2.0)

add_subdirectory(src)
