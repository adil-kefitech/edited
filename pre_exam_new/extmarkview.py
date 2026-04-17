# import json

import ast
import json
from django.db.models import Prefetch
from django.utils import timezone
from iteration_utilities import unique_everseen
from venv import create
from datetime import timedelta

# from numpy import delete
from rest_framework import status  # basically sent back status
from rest_framework.generics import ListAPIView
from river.models import State
from simple_history.utils import bulk_create_with_history,bulk_update_with_history
from academic.serializers import (
    AcademicCourseSerializer,
    AcademicProgrammeSemesterListSerializers,
    CollegeDistrictSerializer,
    CollegeProgramSerializer,
    CollegeTypeSerializer,
    SubsectionProgramGroupSerializer,
    SubsectionProgramSerializer,
    SubsectionProgramTypeSerializer,
    CollegenewDistrictSerializer
)
from util.constants import *

from util.models import *
   
from util.serializers import *


class Extmarkchairmanview(ListAPIView):
    """Course Mapping class view."""

    def get(self, request):
        try:

            user = request.user
            four_months_ago = timezone.now() - timedelta(days=100)
            userids=ExtTeacherAllocation.objects.filter(status_id=80,created_on__gte=four_months_ago).all()
            print("////////",userids)

            fullnames=[]
            for i in userids:
                id= i.user_id
                
                fullnames.append(id)
            print("////////",fullnames)

            usernameobj = User.objects.filter(id__in=fullnames).all()
                
            print("////////",usernameobj)

            userobj=UserSerializer(usernameobj, many=True).data
            userobj = list(unique_everseen(userobj))
            print("////////",userobj)
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={
                    
                    "userobj": userobj,
                    
                    
                },
                status_code=status.HTTP_200_OK,
                template_name="extmarkview.html",
            )
        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

class ExtzoneviewFetch(ListAPIView):
    def post(self, request):
        try:

            user = request.user
            chairman = request.data.get("chairman")
            print("////////",chairman)
            four_months_ago = timezone.now() - timedelta(days=100)

            extteachobj=ExtTeacherAllocation.objects.filter(parent_id=chairman,created_on__gte=four_months_ago).all()
            print("////////",extteachobj)

            fullnames=[]
            for i in extteachobj:
                id= i.user_id
                
                fullnames.append(id)
            print("////////",fullnames)

            usernameobj = User.objects.filter(id__in=fullnames).all()
                
            print("////////",usernameobj)

            userobj=UserSerializer(usernameobj, many=True).data
            userobj = list(unique_everseen(userobj))
            print("////////",userobj)
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={"userobj": userobj},
                status_code=status.HTTP_200_OK,
                template_name="extmarkview.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

class ExttchviewFetch(ListAPIView):
    def post(self, request):
        try:
            user = request.user
            zonechairman = request.data.get("zonechairman")
            print("8888888888", zonechairman)
            four_months_ago = timezone.now() - timedelta(days=100)

            extteachobj = ExtTeacherAllocation.objects.filter(parent_id=zonechairman,created_on__gte=four_months_ago).all()
            print("////////", extteachobj)

            usr_lst = []
            op_data = []
            
            for i in extteachobj:
                usr_id = i.user_id

                user_obj = User.objects.filter(id=usr_id).first()
                username = user_obj.username
                firstname = user_obj.first_name
                lastname = user_obj.last_name
                fullname = f"{firstname} {lastname}"

                prgm_cors_sem_id = i.prgm_cors_sem_id
                corsid = ProgrammeCourseSemester.objects.filter(id=prgm_cors_sem_id).first().course_id
                corsname = CourseMaster.objects.filter(id=corsid).first().name

                collbatchprgsem = i.collegebatch_prgm_sem_id
                colbatchprg = CollegeBatchProgrammeSemester.objects.filter(id=collbatchprgsem).first().college_batch_prgm_id
                colgprg = CollegeBatchProgramme.objects.filter(id=colbatchprg).first().college_programm_id
                colldeptid = CollegeProgramme.objects.filter(id=colgprg).first().college_department_id
                collid = CollegeDepartment.objects.filter(id=colldeptid).first().college_id
                collname = AffiliatedCollege.objects.filter(id=collid).first().name

                if usr_id in usr_lst:
                    # User already exists, append the new college and course name to the existing lists
                    for item in op_data:
                        if item['username'] == username:
                            item['college'].append(collname)
                            item['corsnames'].append(corsname)
                            break
                else:
                    # New user, create a new entry in op_data
                    output_data = {
                        "username": username,
                        "fullname": fullname,
                        "college": [collname],
                        "corsnames": [corsname]
                    }
                    usr_lst.append(usr_id)
                    op_data.append(output_data)
                    print("UUUUSSSSEEEERRR  : ", username, "DDDDDDDDDDDDD : ", collname)

            # Remove duplicates in the college and course names lists
            for item in op_data:
                item['college'] = list(set(item['college']))
                item['corsnames'] = list(set(item['corsnames']))

            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={"result": op_data},
                status_code=status.HTTP_200_OK,
                template_name="extmarkview.html",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
class Exttchviewedit(ListAPIView):
    def post(self, request):
        try:
            print("?????????????")
            # Log the incoming request data for debugging
            

            # If using Django REST Framework, use request.data, otherwise use request.POST
            userids = request.POST.get("userids")  # For plain Django
            print("userid",userids)
            userid=User.objects.filter(username=str(userids)).first().id
            if not userid:
                return JsonResponse({
                    "success": False,
                    "message": "User ID is required",
                    "data": {},
                }, status=status.HTTP_400_BAD_REQUEST)

            # Perform deletion
            deleted_count, _ = ExtTeacherAllocation.objects.filter(user_id=userid).delete()

            if deleted_count > 0:
                return JsonResponse({
                    "success": True,
                    "message": "Examiner(s) deleted successfully",
                    "data": {},
                }, status=status.HTTP_200_OK)
            else:
                return JsonResponse({
                    "success": False,
                    "message": "No matching records found",
                    "data": {},
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error during deletion: {str(e)}")
            return JsonResponse({
                "success": False,
                "message": "An error occurred",
                "data": {},
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
