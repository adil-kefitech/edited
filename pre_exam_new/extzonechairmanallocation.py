# import json

import ast
import json
from django.db.models import Prefetch
from django.utils import timezone
from iteration_utilities import unique_everseen
from venv import create

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


class Extcordchairman(ListAPIView):
    """Course Mapping class view."""

    def get(self, request):
        try:

            user = request.user

            userids=ExtTeacherAllocation.objects.filter(status_id=80).all()
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
                template_name="extzonechairmanallocation.html",
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

class ExtzoneCollegesFetch(ListAPIView):
    def post(self, request):
        try:

            user = request.user
            chairman = request.data.get("chairman")
            print("////////",chairman)
          
            extteachobj=ExtTeacherAllocation.objects.filter(user_id=chairman).all()
            print("////////",extteachobj)

            college=[]
            for extteach in extteachobj:
                college_id=extteach.college_id
                college.append(college_id)
            
            clg_prgms=AffiliatedCollege.objects.filter(id__in=college).all()
            print("////////",clg_prgms)
  
            clgs = CollegenewDistrictSerializer(clg_prgms, many=True).data
            clgs = unique_everseen(clgs)
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={"colleges": clgs},
                status_code=status.HTTP_200_OK,
                template_name="extzonechairmanallocation.html",
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
class ExtzoneFetch(ListAPIView):
    def post(self, request):
        try:
            jsondata = request.data
            search_id = jsondata["search_id"]
            print("2222222222",search_id)


            if "@" in search_id:  # Check if it's an email
                userobj = User.objects.filter(email=str(search_id)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(search_id)).first()
                userobj = User.objects.filter(id=usernameobj.user_id).first()
                print("////////",userobj)

            if userobj:
                usernameobj = User.objects.filter(id=userobj.id).first()
                print("////////",usernameobj)

                
                teachobj=TeacherBase.objects.filter(user_id=userobj.id).first()
                print("////////",teachobj)
               
                collteachobj=CollegeTeacher.objects.filter(teacher_id=teachobj.id).first().college_id
                
                collobjects=AffiliatedCollege.objects.filter(id=collteachobj).first()
                collobj=collobjects.name
                print("////////",collobj)


                
                mail_id = usernameobj.email
                username=usernameobj.username
                first_name = usernameobj.first_name
                last_name = usernameobj.last_name
                fullname = f"{first_name} {last_name}"
                print("////////",fullname)

                return format_response(True,PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,data={"fullname": fullname,"mail_id": mail_id,"collobj":collobj},status_code=status.HTTP_201_CREATED,template_name='extzonechairmanallocation.html')

               
            else:
                return format_response({"message": "User not found"}, status=status.HTTP_NOT_FOUND)
        except Exception as e:
            print(e)
            return format_response(
                {"message": "An error occurred"},
                status=status.HTTP_400_BAD_REQUEST
            )





class ExtzoneUpload(ListAPIView):
    
    def post(self, request):
        try:
          
            print("Raw request data:", request.data)

            search_id = request.data.get("search")
            parentid = request.data.get("cord")
            print("Parent ID:", parentid)

            college_codes_list = request.data.get('college_codes')
            print("College Codes:", college_codes_list)
            if "@" in search_id:  # Check if it's an email
                userobj = User.objects.filter(email=str(search_id)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(search_id)).first()
                userobj = User.objects.filter(id=usernameobj.user_id).first()
                
            if userobj:
                usernameobj = User.objects.filter(id=userobj.id).first()
                userid=usernameobj.id
            
            created_by = request.user
            created_on = timezone.now
           

            user = request.user
            created_by = user
            created_on = timezone.now()

            saved_colleges = []
            for i in college_codes_list:
                i=int(i)
                collobj= AffiliatedCollege.objects.filter(id=i).first()
               
                
                
                extteachobjcheck=ExtTeacherAllocation.objects.filter(user_id=userid,college_id=i).first()
               
                if not extteachobjcheck:
                    collobj= AffiliatedCollege.objects.filter(id=i).first()
                    userobj.groups.add(51)

                  
                   
                   
                    saved_colleges.append(ExtTeacherAllocation(
                            created_on=timezone.now(),
                            created_by=created_by,
                            college_id=collobj.id,
                            user_id=userid,
                            parent_id=parentid,
                            status_id=81
                           
                        ))
                   
                   
                    

            if saved_colleges:
                ExtTeacherAllocation.objects.bulk_create(saved_colleges)

                return format_response(True, ZONAL_SUCCSS_MSG, status_code=status.HTTP_200_OK, template_name='extzonechairmanallocation.html')
            else:
                return format_response({"success": False, "message": COLLEGE_ALREADY_UPLOADED}, status=status.HTTP_200_OK, template_name="extzonechairmanallocation.html",)
        except Exception as e:
            # Handle exceptions appropriately
            print(e)
            return format_response(False, str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
#