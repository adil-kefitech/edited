from rest_framework import serializers #importing restfrmaework
from.models import * # importing modeles we created
import datetime
from datetime import datetime as dt
from util.constants import * 
import base64
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from rest_framework import serializers #importing restfrmaework
from util.models import * # importing modeles we created
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.http import JsonResponse
from django.db.models import F
from functools import reduce
from iteration_utilities import unique_everseen

import threading
from django.db.models import Q
from simple_history.utils import bulk_create_with_history,bulk_update_with_history
from base64 import b64decode
import os








class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields =['name']

#=============================================================#
#          EXAM CREATION SERILIZER                            #
#=============================================================#

class ExaminationCreateSerializer(serializers.ModelSerializer):
   
   
    class Meta:
        model = Examination
        fields = ["title","exam_type","question_paper_delivery_type","season","month","year"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
           
        }
    def create(self,validated_data):
        
        request=self.context['request']
       
        jsondata=request.data
        purpose_list=jsondata.get('purpose_list')
        
        purpose_list_new = json.loads(purpose_list)
        
        notification_url =  jsondata.get('my_file')
        encodedZip = base64.b64encode(notification_url.read())

        pdf = encodedZip

        bytes = b64decode(pdf, validate=True)

        # # Perform a basic validation to make sure that the result is a valid PDF file

        # # Be aware! The magic number (file signature) is not 100% reliable solution to validate PDF files

        # # Moreover, if you get Base64 from an untrusted source, you must sanitize the PDF contents

        # if bytes[0:4] != b'%PDF':

        #     raise ValueError('Missing the PDF file signature')



        prgm_sem_data=jsondata.get('programme_semester')
        prgm = jsondata.get('programme')
        sem = jsondata.get('semester')
        scheme_data =jsondata.get('scheme')
        admission_year_list=jsondata.get('admission_year_list')
        code = self.context['code']
        user = request.user.id
        status_fetch=State.objects.filter(label='PENDING').first()
        admission_improvement=jsondata.get('admissionimprovement')
        notif_title = jsondata.get('notif_title')
        order_number = jsondata.get('order_number')
        notif_date = jsondata.get('notif_date')
        attendance_upload_end_date = jsondata.get('attendance_upload_end_date')
        attendance_regular_list = jsondata.get('admissionyear_regular_list')
        print("attendance_regular_listattendance_regular_listattendance_regular_list",attendance_regular_list)

        exam = [Examination(title=validated_data['title'],code=code,exam_type=validated_data['exam_type'],question_paper_delivery_type=validated_data['question_paper_delivery_type'],season=validated_data['season'],month=validated_data['month'],year=validated_data['year'],created_by_id=user,comments="Exam created",status=status_fetch)]
        objs = bulk_create_with_history(exam, Examination, batch_size=500)
     
        for exm in objs:
            exam_data = exm
        
       
        prgm_sem = [ExamProgrammeSemesterMapping(exam=exam_data,programme_semester_id=prgm_sem_data,scheme_id=scheme_data,created_by_id=user,comments="Exam programme sem created",status=status_fetch)for x in objs]
        prgm_sem_objs = bulk_create_with_history(prgm_sem, ExamProgrammeSemesterMapping, batch_size=500)
        
        add_yr_list = []
        
        for x in admission_year_list:
            if x!=',':
                add_yr_list.append(x)
        # list(map(lambda x:add_yr_list.append(AdmissionYearMaster.objects.get(id=x)),admission_year_list))
        # adm_yr = [ExaminationAdmissionYear(exam=exam_data,admission_year=x,created_by_id=user,comments="Exam AdmissionYear created",status=status_fetch)for x in add_yr_list]

        # adm_yr = [ExaminationAdmissionYear(exam=exam_data,admission_year_id=x,created_by_id=user,comments="Exam AdmissionYear created",status=status_fetch)for x in add_yr_list]
        if admission_improvement is not None:
            adm_yr=[]
            improvmnt_admission_year=AdmissionYearMaster.objects.get(id=admission_improvement)
            for x in add_yr_list:
                if x==str(improvmnt_admission_year.id):
                    exam_admission_year = ExaminationAdmissionYear(exam=exam_data,admission_year_id=x,created_by_id=user,comments="Exam AdmissionYear created improv",improvement=True,status=status_fetch,Regular=False)
                    adm_yr.append(exam_admission_year)
                else:
                    if x in attendance_regular_list: 
                        exam_admission_year = ExaminationAdmissionYear(exam=exam_data,admission_year_id=x,created_by_id=user,comments="Exam AdmissionYear created try",improvement=False,status=status_fetch,Regular=True)
                        adm_yr.append(exam_admission_year)
                    else:
                        exam_admission_year = ExaminationAdmissionYear(exam=exam_data,admission_year_id=x,created_by_id=user,comments="Exam AdmissionYear created try",improvement=False,status=status_fetch,Regular=False)
                        adm_yr.append(exam_admission_year)
        else:
            adm_yr = [ExaminationAdmissionYear(exam=exam_data,admission_year_id=x,created_by_id=user,comments="Exam AdmissionYear created",improvement=False,status=status_fetch,Regular=True if x in attendance_regular_list else False)for x in add_yr_list]
        objs = bulk_create_with_history(adm_yr, ExaminationAdmissionYear, batch_size=500)
        purp_list=[]
        puspose_start_date = []
        purpose_end_list = []
        list(map(lambda y:purp_list.append(ExaminationPurposeMaster.objects.get(id=y.get('purposeId'))),purpose_list_new))

        list(map(lambda strt_date:puspose_start_date.append(strt_date.get('startDate')),purpose_list_new))

        list(map(lambda end_date:purpose_end_list.append(end_date.get('endDate')),purpose_list_new))
       
        
        exam_date = [ExaminationDate(exam=exam_data,purpose=y,start_date=x,end_date=n,created_by_id=user,comments="Exam purpose Date created",status=status_fetch)for y,x,n in zip(purp_list,puspose_start_date,purpose_end_list)]
        objs = bulk_create_with_history(exam_date, ExaminationDate, batch_size=500)


        notification = [ExaminationNotification(title=notif_title,date=notif_date,order_number=order_number,attendance_upload_end_date=attendance_upload_end_date,notification_url=pdf,exam_prgm_sem=x,created_by_id=user,comments="Exam Notification created",status=status_fetch)for x in prgm_sem_objs]
        notif_objs = bulk_create_with_history(notification, ExaminationNotification, batch_size=500)

       
        
        
        return exam




#============================Programme Master Serializers===================================================================
class ProgrammeMasterSerializers(serializers.ModelSerializer):
    
    class Meta:
        model=Programme
        fields=["id","code","title","short_description","description","programme_class","programme_type","programme_group","programme_duration","programme_duration_count"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }

#=========================Programme Class Master Serializers================================================
class ProgrammeClassMasterSerializers(serializers.ModelSerializer):
    class Meta:
        model=ProgrammeClassMaster

        fields=["id","title","code","description"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }

#===========================Programme Type Master Serializers=================================================
class ProgrammeTypeMasterSerializers(serializers.ModelSerializer):
    class Meta:
        model=ProgrammeTypeMaster

        fields=["id","code","title","description"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }
#===========================Programme Group Master Serializers=======================================================
class ProgrammeGroupMasterSerializers(serializers.ModelSerializer):
    class Meta:
        model=ProgrammeGroupMaster

        fields=["id","title","code","description"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }


class ExaminationTypeMasterSerializer(serializers.ModelSerializer):
    
    class Meta:
        
        model=ExaminationTypeMaster
        fields=["id","name"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }  
# ==================Get Exam Question Paper Delivery types =======================#

class ExamQpDeliverySerializer(serializers.ModelSerializer):
    
    class Meta:
        
        model=ExaminationQuestionPaperDeliveryMaster
        fields=["id","name"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }  

class ExaminationPurposeSerializer(serializers.ModelSerializer):
    
    class Meta:
        
        model=ExaminationPurposeMaster
        fields=["id","name"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }  
        
class ProgrammeClassSerializer(serializers.ModelSerializer):
    class Meta :
    
        model = ProgrammeClassMaster

        fields = ["id","title","code"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
        }
class ProgrammeGroupSerializer(serializers.ModelSerializer):
    class Meta :
    
        model = ProgrammeGroupMaster

        fields = ["id","title","code"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
        }


#==============================================================#
#           EXAM LIST SERIALIZER START                         #
#==============================================================#

class ExamAdmissionYearSerializer(serializers.ModelSerializer):
    admission_year=serializers.CharField(source="admission_year.admission_year")
    class Meta:
        model = ExaminationAdmissionYear

        fields = ["admission_year"]


        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'status':{}
            }


class ExamPrgSemListSerializer(serializers.ModelSerializer):
    programme=serializers.CharField(source="programme_semester.programme.title")
    programme_code=serializers.CharField(source="programme_semester.programme.code")
    semester=serializers.CharField(source="programme_semester.semester.title")
    scheme=serializers.CharField(source="scheme.name")
    programme_type=serializers.CharField(source="programme_semester.programme.programme_type.title")
    programme_group=serializers.CharField(source="programme_semester.programme.programme_group.title")
    programme_class=serializers.CharField(source="programme_semester.programme.programme_class.title")
    class Meta:
        model = ExamProgrammeSemesterMapping

        fields = ["scheme","semester","programme","programme_type","programme_group","programme_class","programme_code"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }



class ExamListSerializer(serializers.ModelSerializer):
 
    exam_type=serializers.CharField(source="exam_type.name")
    season=serializers.CharField(source="season.title")
    qp_delivery_type=serializers.CharField(source="question_paper_delivery_type.name")
    admission_yr=ExamAdmissionYearSerializer(many=True)
    prgm_details=ExamPrgSemListSerializer(many=True)
    status = serializers.CharField(source="status.label")
    class Meta:
        model = Examination

        fields = ["id","title","exam_type","qp_delivery_type","season","month","year","code","prgm_details","admission_yr","status"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'code':{},
            'status':{}
            }
    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.prefetch_related('admission_yr','prgm_sem','prgm_details')
        return queryset

#==============================================================#
#           EXAM LIST SERIALIZER END                           #
#==============================================================#


#==============================================================#
#           EXAM NOTIFIVATION SERIALIZER START                 #
#==============================================================#

class ExamNotificationviewSerailizer(serializers.ModelSerializer):
    
    
    notif_date=serializers.DateField(source="date",format="%d-%m-%Y")
    attendance_end_date = serializers.DateField(source="attendance_upload_end_date",format="%d-%m-%Y")
    programme_name=serializers.CharField(source="exam_prgm_sem.programme_semester.programme.title")
    semester=serializers.CharField(source="exam_prgm_sem.programme_semester.semester.title")
    created_by = serializers.SerializerMethodField()
    label=serializers.CharField(source="status.label")
    created_on=serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
    class Meta:
        model=ExaminationNotification
        fields=["id","title","notif_date","attendance_end_date","order_number","programme_name","semester","status_id","label","created_on","created_by","updated_on","comments"]   
    
    extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }
    def get_created_by(self,object):
        user=User.objects.filter(id=object.created_by.id).first()
        return user.get_full_name()




#==============================================================#
#           EXAM NOTIFIVATION SERIALIZER END                   #
#==============================================================#


#==============================================================#
#           EXAM SINGLE GET SERIALIZER START                   #
#==============================================================#


class FeeSerializer(serializers.ModelSerializer):
    fee_param=serializers.CharField(source="fee_parameter.name")
    fee_cat=serializers.CharField(source="fee_category.name")
    class Meta:
        
        model=FeeDefinition
        fields=["id","fee_param","fee_cat","amount"]

        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
        }  

class ProgrammeSemesterExamSerializer(serializers.ModelSerializer):
    programme=serializers.CharField(source='programme.name')
    semester_id=serializers.CharField(source='semester.id')
    semester=serializers.CharField(source='semester.title')
    # fee_list=FeeSerializer(many=True)
    # fee_list_data = serializers.SerializerMethodField()
    class Meta:
        model = ProgrammeSemester

        fields = ["programme","semester_id","semester"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }
    # def get_fee_list_data(self,object):
        
    #     fee_data =FeeDefinition.objects.filter(programme_semester=object.id).order_by('fee_parameter__name')
   
    #     fee_data_serial=FeeSerializer(fee_data,many=True)
    #     return fee_data_serial.data


class SchemeMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeMaster

        fields = ["id","title"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True}
            
            }


class ExamScheduleSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    courseCode = serializers.SerializerMethodField()   # ✓ already added
    prgm = serializers.CharField(source='programme_semester_course.programme_semester.programme.title')
    sem = serializers.CharField(source='programme_semester_course.programme_semester.semester.title')
    course_exam_type = serializers.CharField(source='exam_type.name')
    start_date = serializers.DateField(format="%d-%m-%Y")
    end_date = serializers.DateField(format="%d-%m-%Y")

    class Meta:
        model = ExaminationSchedule
        # ADD "courseCode" to this list:
        fields = ["id", "programme_semester_course", "prgm", "sem", "start_date", "end_date", "start_time", "end_time", "course", "courseCode", "course_exam_type"]
        extra_kwargs = {
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True}
        }

    def get_course(self, obj):
        if obj.programme_semester_course.sub_course:
            return obj.programme_semester_course.course.name + " (" + obj.programme_semester_course.sub_course.name + ")"
        else:
            return obj.programme_semester_course.course.name

    def get_courseCode(self, obj):
        return obj.programme_semester_course.course.code
    def get_courseCode(self, obj):
        return obj.programme_semester_course.course.code


class ExamDateSerializer(serializers.ModelSerializer):
    purpose_name=serializers.CharField(source='purpose.name')
    title=serializers.CharField(source='exam.title')
    start_date = serializers.DateField(format="%d-%m-%Y")
    end_date = serializers.DateField(format="%d-%m-%Y")
    status=serializers.CharField(source='status.label')
    class Meta:
        model = ExaminationDate
        fields = ["purpose_name","start_date","end_date","title","status"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'exam':{},
            'status':{}
            }

class ExamAdmissionYearSerializer(serializers.ModelSerializer):
    admission_year=serializers.CharField(source="admission_year.admission_year")
    class Meta:
        model = ExaminationAdmissionYear

        fields = ["admission_year"]


        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'status':{}
            }
class ExamNotifSerializer(serializers.ModelSerializer):

    date = serializers.DateField(format="%d-%m-%Y")
    attendance_upload_end_date = serializers.DateField(format="%d-%m-%Y")
    
    class Meta:
        model = ExaminationNotification

        fields = ["title","date","attendance_upload_end_date"]


        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'status':{}
            }
# class ExamEditNotifSerializer(serializers.ModelSerializer):
#     date_data = serializers.DateField(source="date",format="%d/%m/%Y")
#     attendance_upload_end_date_data = serializers.DateField(source="attendance_upload_end_date",format="%d/%m/%Y")
#     class Meta:
#         model = ExaminationNotification

#         fields = [
#             "title", "date_data", "order_number", 
#             "attendance_upload_end_date_data", "created_on", 
#             "updated_on", "created_by", "updated_by", "status"
#             ]
        
#         extra_kwargs ={
#             'created_on': {'write_only': True},
#             'updated_on': {'write_only': True},
#             'created_by': {'write_only': True},
#             'updated_by': {'write_only': True},
#             'status':{}
#             }


class ExamEditNotifSerializer(serializers.ModelSerializer):
    date_data = serializers.DateField(source="date", format="%d/%m/%Y")
    attendance_upload_end_date_data = serializers.DateField(source="attendance_upload_end_date", format="%d/%m/%Y")
    has_document = serializers.SerializerMethodField()

    def get_has_document(self, obj):
        # Memory-Safe Check: Returns True if there is data, without loading the whole file into RAM
        if not obj.notification_url:
            return False
        return bool(obj.notification_url)
        
    class Meta:
        model = ExaminationNotification
        # Strictly the fields your examedit.html template needs
        fields = [
            "has_document", 
            "title", 
            "date_data", 
            "order_number", 
            "attendance_upload_end_date_data"
        ]
        # Notice: extra_kwargs is completely removed!

class ExamProgrammeSemesterMappingSerializer(serializers.ModelSerializer):
    programme_id=serializers.CharField(source="programme_semester.programme.id")
    programme=serializers.CharField(source="programme_semester.programme.title")
    programme_code=serializers.CharField(source="programme_semester.programme.code")
    semester_id=serializers.CharField(source="programme_semester.semester.id")
    semester=serializers.CharField(source="programme_semester.semester.title")
    scheme_id=serializers.CharField(source="scheme.id")
    scheme=serializers.CharField(source="scheme.name")
    programme_type=serializers.CharField(source="programme_semester.programme.programme_type.title")
    notif_prgm_sem = ExamNotifSerializer(many=True)
    class Meta:
        model = ExamProgrammeSemesterMapping

        fields = ["scheme","semester","programme","scheme_id","semester_id","programme_id","programme_type","programme_code","notif_prgm_sem"]        
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }


class ExamSerializer(serializers.ModelSerializer):
    purpose_list=ExamDateSerializer(many=True)
    schedule_list=ExamScheduleSerializer(many=True)
    exam_type=serializers.CharField(source="exam_type.name")
    season=serializers.CharField(source="season.title")
    qp_delivery_type=serializers.CharField(source="question_paper_delivery_type.name")
    admission_yr=ExamAdmissionYearSerializer(many=True)
    prgm_sem=ProgrammeSemesterExamSerializer(many=True)
    prgm_details=ExamProgrammeSemesterMappingSerializer(many=True)
    status = serializers.CharField(source='status.label')
    sch_status = serializers.SerializerMethodField()
    purpose_status = serializers.SerializerMethodField()
    class Meta:
        model = Examination

        fields = ["id","sch_status","purpose_status","title","exam_type","qp_delivery_type","season","month","year","code","purpose_list","schedule_list","prgm_details","admission_yr","prgm_sem","status"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'code':{},
            'status':{}
            }
    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.prefetch_related('admission_yr','prgm_sem','prgm_details')
        return queryset
    def get_sch_status(self,object):
        exm_schld =ExaminationSchedule.objects.filter(exam=object.id,status__label__in=["ACTIVE","PENDING"])
        exm_schld_serial=ExamScheduleSerializer(exm_schld,many=True)
        return exm_schld_serial.data

    def get_purpose_status(self,object):
        exm_purpo =ExaminationDate.objects.filter(exam=object.id,status__label__in=["ACTIVE","PENDING"])
        exm_purpo_serial=ExamDateSerializer(exm_purpo,many=True)
        return exm_purpo_serial.data


class ExaminationHistorySerializer(serializers.ModelSerializer):
     updated_by = serializers.SerializerMethodField()
     created_by = serializers.SerializerMethodField()
     designation = GroupSerializer(source='history_user.groups',many=True)
     updated_on = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_on = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     class Meta:       
       model =   HistoricalExamination
       fields = ["id","comments","created_by","created_on","designation","history_user","updated_by","updated_on"]
     def get_updated_by(self,object):
         user=User.objects.filter(id=object.history_user.id).first()
         return user.get_full_name()
     def get_created_by(self,object):
         user=User.objects.filter(id=object.created_by.id).first()
         return user.get_full_name()

class ProgrammeSemesterExamFeeSerializer(serializers.ModelSerializer):
    programme=serializers.CharField(source='programme.name')
    semester=serializers.CharField(source='semester.title')
    # fee_list=FeeSerializer(many=True)
    fee_list_data = serializers.SerializerMethodField()
    prgsem_id = serializers.CharField(source='id')
    class Meta:
        model = ProgrammeSemester

        fields = ["prgsem_id","programme","fee_list_data","semester"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }
    def get_fee_list_data(self,object):
        
        fee_data =FeeDefinition.objects.filter(programme_semester=object.id).order_by('fee_parameter__name')
        
        fee_data_serial=FeeSerializer(fee_data,many=True)
        return fee_data_serial.data

class ExamFeeFtechSerializer(serializers.ModelSerializer):
    
    
    prgm_sem=ProgrammeSemesterExamFeeSerializer(many=True)
    
    class Meta:
        model = Examination

        fields = ["id","prgm_sem"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'code':{},
            'status':{}
            }
class FeeCategoryserilizer(serializers.ModelSerializer):
    class Meta:
    
        model=FeeCategory
        fields=["id","title","code","name"]
        extra_kwargs = {
        'created_on': {'write_only': True},
        'updated_on': {'write_only': True},
        'created_by': {'write_only': True},
        'updated_by': {'write_only': True},
    
    } 

class ExamSingleFtechSerializer(serializers.ModelSerializer):
    
    exam_type=serializers.CharField(source="exam_type.name")
    season=serializers.CharField(source="season.title")
    qp_delivery_type=serializers.CharField(source="question_paper_delivery_type.name")
    admission_yr=ExamAdmissionYearSerializer(many=True)
    prgm_sem=ProgrammeSemesterExamSerializer(many=True)
    prgm_details=ExamProgrammeSemesterMappingSerializer(many=True)
    status = serializers.CharField(source='status.label')
    # sch_status = serializers.SerializerMethodField()
    purpose_status = serializers.SerializerMethodField()
    class Meta:
        model = Examination

        fields = ["id","purpose_status","title","exam_type","qp_delivery_type","season","month","year","code","prgm_details","admission_yr","prgm_sem","status"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'code':{},
            'status':{}
            }
    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.prefetch_related('admission_yr','prgm_sem','prgm_details')
        return queryset
    # def get_sch_status(self,object):
    #     exm_schld =ExaminationSchedule.objects.filter(exam=object.id,status__label__in=["ACTIVE","PENDING"])
    #     exm_schld_serial=ExamScheduleSerializer(exm_schld,many=True)
    #     return exm_schld_serial.data

    def get_purpose_status(self,object):
        exm_purpo =ExaminationDate.objects.filter(exam=object.id,status__label__in=["ACTIVE","PENDING"]).order_by('purpose')
        exm_purpo_serial=ExamDateSerializer(exm_purpo,many=True)
        return exm_purpo_serial.data


#==============================================================#
#           EXAM SINGLE GET SERIALIZER END                     #
#==============================================================#


#============================================================#
#                  EXAM APPROVAL                             #
#============================================================#
def do_approve(obj,next_status,approved_by):

    print(obj.river.status.approve(as_user=approved_by,next_state=next_status))
    obj.river.status.approve(as_user=approved_by,next_state=next_status)
    


class ExamApprovalSerializer(serializers.ModelSerializer):
    approval =serializers.SerializerMethodField()
   
    
    class Meta:
        model = Examination
        fields = ["id","approval"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
           
        }
    def get_approval(self,obj):
        # print("ok")
        exam_id = obj.id
        approved_by=self.context['approved_by']
       
        updated_on=self.context['updated_on']
        text=self.context['text']
        next_status=self.context['next_status']
        status_fetch=State.objects.filter(label=next_status).first()
        schedule=ExaminationSchedule.objects.filter(exam=exam_id).all()
       
        for j in schedule:
            j.comments=text
            j.updated_by=approved_by
            j.updated_on=updated_on
            j.status=status_fetch
            
        bulk_update_with_history(schedule, ExaminationSchedule, ['comments','updated_by','updated_on','status'], batch_size=500)
            
        
        dates=ExaminationDate.objects.filter(exam=exam_id).all()
        for i in dates:
           
            i.comments=text
            i.updated_by=approved_by
            i.updated_on=updated_on
            i.status=status_fetch
        bulk_update_with_history(dates, ExaminationDate, ['comments','updated_by','updated_on','status'],batch_size=500)
   
        admission_year=ExaminationAdmissionYear.objects.filter(exam=exam_id).all()
        for n in admission_year:
            
            n.updated_by=approved_by
            n.comments=text
            n.updated_on=updated_on
            n.status=status_fetch
        bulk_update_with_history(admission_year, ExaminationAdmissionYear, ['comments','updated_by','updated_on','status'], batch_size=500)   
            
    
        prgm_Sem=ExamProgrammeSemesterMapping.objects.filter(exam=exam_id).all()
        for m in prgm_Sem:
            
            m.comments=text
            m.updated_by=approved_by
            m.updated_on=updated_on
            m.status=status_fetch
            
        bulk_update_with_history(prgm_Sem, ExamProgrammeSemesterMapping, ['comments','updated_by','updated_on','status'], batch_size=500)

        notification =ExaminationNotification.objects.filter(exam_prgm_sem__in=prgm_Sem).all()
        
        for p in notification:
            
            p.comments=text
            p.updated_by=approved_by
            p.updated_on=updated_on
            p.status=status_fetch
            
        bulk_update_with_history(notification, ExaminationNotification, ['comments','updated_by','updated_on','status'], batch_size=500)




class ExamDateEditSerializer(serializers.ModelSerializer):
    purpose_name=serializers.CharField(source='purpose.name')
    purpose_id=serializers.CharField(source='purpose.id')
    class Meta:
        model = ExaminationDate
        fields = ["id","purpose_name","start_date","end_date","purpose_id"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'exam':{},
            'status':{}
            }

class ExamProgrammeSemesterMappingEditSerializer(serializers.ModelSerializer):
    programme=serializers.CharField(source="programme_semester.programme.title")
    programme_code=serializers.CharField(source="programme_semester.programme.code")
    semester=serializers.CharField(source="programme_semester.semester.title")
    semester_id=serializers.CharField(source="programme_semester.semester.id")
    programme_type=serializers.CharField(source="programme_semester.programme.programme_type.title")
    scheme_title=serializers.CharField(source="scheme.title")
    class Meta:
        model = ExamProgrammeSemesterMapping
        fields = ["scheme","scheme_title","semester","semester_id","programme","programme_type","programme_code","id"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }

class ExamAdmissionYearEditSerializer(serializers.ModelSerializer):
    admission_year=serializers.CharField(source="admission_year.admission_year")
    admissionid=serializers.CharField(source="admission_year.id")
    class Meta:
        model = ExaminationAdmissionYear

        fields = ["admissionid","admission_year"]


        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'status':{}
            }
class ProgrammeSemesterEditExamSerializer(serializers.ModelSerializer):
    programme=serializers.CharField(source='programme.name')
    programme_id=serializers.CharField(source='programme.id')
    programme_type=serializers.CharField(source='programme.programme_type.title')
    programme_group=serializers.CharField(source='programme.programme_group.title')
    programme_class=serializers.CharField(source='programme.programme_class.title')
    semester=serializers.CharField(source='semester.title')
    fee_list=FeeSerializer(many=True)
    class Meta:
        model = ProgrammeSemester

        fields = ["programme","programme_id","semester","fee_list",'programme_group','programme_class','programme_type']

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }
class ExamScheduleEditSerializer(serializers.ModelSerializer):
    course=serializers.CharField(source='programme_semester_course.course.name')
    courseid=serializers.CharField(source='programme_semester_course.id')
    course_exam_type=serializers.CharField(source='exam_type.name')
    start_date = serializers.DateField(format="%Y-%m-%d")
    end_date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = ExaminationSchedule

        fields = ["id","programme_semester_course","start_date","end_date","time_display_name","start_time","end_time","course","courseid","course_exam_type"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True}
            
            }
class ExamEditSerializer(serializers.ModelSerializer):
    purpose_list=ExamDateEditSerializer(many=True)
    schedule_list=ExamScheduleEditSerializer(many=True)
    exam_type=serializers.CharField(source="exam_type.name")
    exam_type_id=serializers.CharField(source="exam_type.id")
    season=serializers.CharField(source="season.title")
    seasonid=serializers.CharField(source="season.id")
    qp_delivery_type=serializers.CharField(source="question_paper_delivery_type.name")
    qp_delivery_type_id=serializers.CharField(source="question_paper_delivery_type.id")
    admission_yr=ExamAdmissionYearEditSerializer(many=True)
    prgm_sem=ProgrammeSemesterEditExamSerializer(many=True)
    prgm_details=ExamProgrammeSemesterMappingEditSerializer(many=True)
    class Meta:
        model = Examination

        fields = ["id","title","code","exam_type","exam_type_id","qp_delivery_type","qp_delivery_type_id","season","seasonid","month","year","code","purpose_list","schedule_list","prgm_details","admission_yr","prgm_sem"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'code':{},
            'status':{}
            }
    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.prefetch_related('admission_yr','prgm_sem','prgm_details')
        return queryset


class ExamAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Examination

        fields = ["title","exam_type","question_paper_delivery_type","season","month","year"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            'code':{},
            'status':{}
            }

#=====FOR Exam wise Prgm,sem,scheme fetch=========================

class ExamProgrammeSemesterMappingFetchSerializer(serializers.ModelSerializer):
    programme=serializers.CharField(source="programme_semester.programme.name")
    programme_id=serializers.CharField(source="programme_semester.programme.id")
    semester=serializers.CharField(source="programme_semester.semester.title")
    semester_id=serializers.CharField(source="programme_semester.semester.id")
    programme_sem_id=serializers.CharField(source="programme_semester.id")
    scheme_title=serializers.CharField(source="scheme.title")
    exam_title=serializers.CharField(source="exam.title")
    exam_type = serializers.CharField(source="exam.exam_type.name")
    class Meta:
        model = ExamProgrammeSemesterMapping
        fields = ["scheme","exam_type","scheme_title","exam_title","semester","semester_id","programme","programme_id","id","programme_sem_id"]
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }


#========FOR COURSE LIST====================================

class ProgrammeCourseSemesterNew(serializers.ModelSerializer):
    prgm_course_sem_id =serializers.CharField(source='id')
    course_id = serializers.CharField(source='course.id')
    course_name = serializers.SerializerMethodField()
    course_code = serializers.CharField(source='course.code')
    course_type_code = serializers.CharField(source='course.course_type.code')
    duaration = serializers.SerializerMethodField()
    class Meta:
        model=ProgrammeCourseSemester

        fields=["prgm_course_sem_id","course_id","course_name","course_type_code","duaration","course_code"]
        
        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},

        }

    def get_course_name(self,obj):
        if obj.sub_course:
            return obj.course.name +" ("+ obj.sub_course.name +")"
        else:
            return obj.course.name
    def get_duaration(self,obj):
        if obj.sub_course:
            coursparam=CourseParameters.objects.filter(code=EXAM_DURATION_CODE).first()
            coursparamval=CourseParametersProgrammeType.objects.filter(course_parms=coursparam).first()
            coursparamval=CourseParamsValue.objects.filter(course_parms_programme_type=coursparamval,course=obj.course_id,sub_course=obj.sub_course).first()
            if(coursparamval):
                max_mark=coursparamval.course_parmas_value
                return max_mark
            else:
                return "90"
        else:
            coursparam=CourseParameters.objects.filter(code=EXAM_DURATION_CODE).first()
            coursparamval=CourseParametersProgrammeType.objects.filter(course_parms=coursparam).first()
            coursparamval=CourseParamsValue.objects.filter(course_parms_programme_type=coursparamval,course=obj.course_id,sub_course=obj.sub_course).first()
            if(coursparamval):
                max_mark=coursparamval.course_parmas_value
                return max_mark
            else:                
                return "180"    



class SemesterwiseCourse(serializers.ModelSerializer):
    sem_id=serializers.CharField(source='semester.id')
    sem_title=serializers.CharField(source='semester.title')
    prgm_id = serializers.CharField(source='programme.id')
    # sem_code=serializers.CharField(source='semester.code')
    # prgm_cours=ProgrammeCourseSemesterNew(many=True)
    # course_list=CourseSerializer(many=True)
    prgm_course_order = serializers.SerializerMethodField()
   
    
    class Meta:
        model = ProgrammeSemester

        fields = ["id","sem_id","prgm_id","sem_title","prgm_course_order"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True},
            
            }
    def get_prgm_course_order(self,obj):
        try:
            scheme_id = self.context.get('scheme_id')
            exam_reg = self.context.get('exam_reg')
            course_id = []
            course_data_id = []
            course_type_id = [13,38]
            
            schm_obj=SchemeMaster.objects.filter(name=scheme_id).first()
            exam_reg_crs = ExamRegistrationCourseMapper.objects.filter(exam_registration__in = exam_reg).all()
            stud_exm_crs = [regcrs.student_semester_course.prgm_sem_course.id for regcrs in exam_reg_crs]
            stud_crs = list(unique_everseen(stud_exm_crs))
            prgm_course_order = ProgrammeCourseSemester.objects.filter(programme_semester=obj,scheme=schm_obj,id__in = stud_crs,status_id=ACTIVE_STATE).order_by("course_order")
            for prg_cour in prgm_course_order:
                cour_id = prg_cour.course.id
                course_data_id.append(cour_id)
            course_data = CourseMaster.objects.filter(id__in =course_data_id).filter(~Q(course_type__in=course_type_id))

            prgm_sem_cour_final = ProgrammeCourseSemester.objects.filter(programme_semester=obj,course__in=course_data).order_by("course_order")
            prgm_course_order_serl = ProgrammeCourseSemesterNew(prgm_sem_cour_final,many=True)

            return prgm_course_order_serl.data
        
        except Exception as e:
            logger.error(e,exc_info = True)
            return "NA"


#====================================================================#
#           FOR EXAM SCHEDULE SERIALIZER START                       #
#====================================================================#

class ExamRecheduleExamGetSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="status.label")
    exam_id=serializers.CharField(source='exam.id')
    exam_name=serializers.CharField(source='exam.title')
    prgm = serializers.CharField(source='programme_semester_course.programme_semester.programme.title')
    sem = serializers.CharField(source='programme_semester_course.programme_semester.semester.title')
    status = serializers.CharField(source='status.label')
    class Meta:
        model = ExaminationSchedule

        fields = ["id","exam_name","prgm","sem","status","exam_id"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True}
            
            }


class ExaminationScheduleHistorySerializer(serializers.ModelSerializer):
     updated_by = serializers.SerializerMethodField()
     created_by = serializers.SerializerMethodField()
     designation = GroupSerializer(source='history_user.groups',many=True)
     updated_on = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     created_on = serializers.DateTimeField(format="%d-%m-%Y %I:%M:%S %p")
     class Meta:       
       model =   HistoricalExaminationSchedule
       fields = ["id","comments","created_by","created_on","designation","history_user","updated_by","updated_on"]
     def get_updated_by(self,object):
         user=User.objects.filter(id=object.history_user.id).first()
         return user.get_full_name()
     def get_created_by(self,object):
         user=User.objects.filter(id=object.created_by.id).first()
         return user.get_full_name()


class ExamScheduleEditSerializer(serializers.ModelSerializer):
    course=serializers.CharField(source='programme_semester_course.course.name')
    prgm = serializers.CharField(source='programme_semester_course.programme_semester.programme.title')
    sem = serializers.CharField(source='programme_semester_course.programme_semester.semester.title')
    course_exam_type=serializers.CharField(source='exam_type.name')
    start_date = serializers.DateField(format="%Y-%m-%d")
    end_date = serializers.DateField(format="%Y-%m-%d")
    prgm_sem_cours_id = serializers.CharField(source='programme_semester_course.id')
    # status = serializers.SerializerMethodField()
    class Meta:
        model = ExaminationSchedule

        fields = ["id","programme_semester_course","prgm_sem_cours_id","prgm","sem","start_date","end_date","time_display_name","start_time","end_time","course","course_exam_type","status"]

        extra_kwargs ={
            'created_on': {'write_only': True},
            'updated_on': {'write_only': True},
            'created_by': {'write_only': True},
            'updated_by': {'write_only': True}
            
            }


#====================================================================#
#           FOR EXAM SCHEDULE SERIALIZER END                         #
#====================================================================#

