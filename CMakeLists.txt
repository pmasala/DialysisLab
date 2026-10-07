cmake_minimum_required(VERSION 3.16)
project(DialysisLab VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
option(DIALYSISLAB_SANITIZE "Enable address and undefined-behavior sanitizers" OFF)
foreach(service plant control protection)
    add_executable(${service} src/${service}.cpp)
    target_compile_options(${service} PRIVATE -Wall -Wextra -Wpedantic -Werror -fno-fast-math
        "-ffile-prefix-map=${CMAKE_SOURCE_DIR}=." "-ffile-prefix-map=${CMAKE_BINARY_DIR}=build")
    if(DIALYSISLAB_SANITIZE)
        target_compile_options(${service} PRIVATE -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer)
        target_link_options(${service} PRIVATE -fsanitize=address,undefined)
    endif()
endforeach()
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
file(GLOB identity_inputs CONFIGURE_DEPENDS src/*.cpp src/*.hpp python/dialysislab/*.py scenarios/*.json)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${identity_inputs} tools/build_identity.py)
execute_process(COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tools/build_identity.py
    --output ${CMAKE_BINARY_DIR}/build_identity.json --compiler-id ${CMAKE_CXX_COMPILER_ID}
    --compiler-version ${CMAKE_CXX_COMPILER_VERSION} --build-type "${CMAKE_BUILD_TYPE}"
    RESULT_VARIABLE identity_status)
if(NOT identity_status EQUAL 0)
    message(FATAL_ERROR "Cannot record build identity")
endif()
enable_testing()
add_test(NAME assurance_and_m1 COMMAND ${Python3_EXECUTABLE} -m unittest discover -s tests -v)
set_tests_properties(assurance_and_m1 PROPERTIES WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    ENVIRONMENT "DIALYSISLAB_BUILD_DIR=${CMAKE_BINARY_DIR};PYTHONPATH=${CMAKE_SOURCE_DIR}/python")
